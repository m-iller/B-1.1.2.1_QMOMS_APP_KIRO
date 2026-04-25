import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ForbiddenException, NotFoundException
from app.common.roles import TASK_ACTIVATION_ROLES, TASK_VALIDATOR_ROLES
from app.modules.notification.service import NotificationService
from app.modules.task import repository
from app.modules.task.schemas import CreateTaskRequest, TaskResponse, UpdateTaskRequest

logger = logging.getLogger(__name__)

_notification_service = NotificationService()


def _compute_overdue(task) -> bool:
    """Return True if task deadline has passed and task is not completed/validated."""
    if task.state in ("completed", "validated"):
        return False
    try:
        deadline = task.deadline
        if isinstance(deadline, str):
            deadline = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        return deadline < datetime.now(timezone.utc)
    except (ValueError, TypeError) as exc:
        logger.warning("Failed to compute overdue for task %s: %s", getattr(task, "id", "?"), exc)
        return False


def _to_response(task) -> TaskResponse:
    return TaskResponse(
        id=str(task.id),
        machine_id=str(task.machine_id),
        title=task.title,
        description=task.description,
        priority=task.priority,
        state=task.state,
        deadline=task.deadline,
        pending_activation=task.pending_activation,
        overdue=_compute_overdue(task),
        created_by=str(task.created_by) if task.created_by else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


async def find_all(machine_id: str | None, state: str | None, db: AsyncSession) -> list[TaskResponse]:
    tasks = await repository.get_all_tasks(machine_id, state, db)
    return [_to_response(t) for t in tasks]


async def find_by_id(task_id: str, db: AsyncSession) -> TaskResponse:
    task = await repository.get_task_by_id(task_id, db)
    if task is None:
        raise NotFoundException(f"Task {task_id} not found")
    return _to_response(task)


async def create(payload: CreateTaskRequest, actor, db: AsyncSession, event_service=None) -> TaskResponse:
    task = await repository.create_task(
        machine_id=payload.machine_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        deadline=payload.deadline,
        created_by=actor.id,
        db=db,
    )

    if event_service:
        try:
            await event_service.emit(
                machine_id=payload.machine_id,
                event_type="TASK_CREATED",
                payload={"task_id": str(task.id)},
                db=db,
            )
        except Exception as exc:
            logger.warning("Event emit failed for TASK_CREATED task=%s: %s", task.id, exc)

    try:
        await _notification_service.notify_task_created(task, db)
    except Exception as exc:
        logger.warning("Notification failed for task_created task=%s: %s", task.id, exc)

    return _to_response(task)


async def update_state(
    task_id: str,
    payload: UpdateTaskRequest,
    actor,
    db: AsyncSession,
    event_service=None,
) -> TaskResponse:
    task = await repository.get_task_by_id(task_id, db)
    if task is None:
        raise NotFoundException(f"Task {task_id} not found")

    new_state = payload.state
    if new_state is None:
        return _to_response(task)

    previous_state = task.state

    # Operator requesting activation → set pending_activation flag, state unchanged
    if new_state == "active" and actor.role == "operator":
        task = await repository.set_pending_activation(task_id, True, db)
        return _to_response(task)

    if new_state == "validated" and actor.role not in TASK_VALIDATOR_ROLES:
        raise ForbiddenException("Only dispatchers can validate tasks")

    task = await repository.update_task_state(task_id, new_state, db)

    if new_state == "completed" and event_service:
        try:
            await event_service.emit(
                machine_id=str(task.machine_id),
                event_type="TASK_COMPLETED",
                payload={"task_id": task_id},
                db=db,
            )
        except Exception as exc:
            logger.warning("Event emit failed for TASK_COMPLETED task=%s: %s", task_id, exc)

    try:
        await _notification_service.notify_task_state_changed(task, previous_state, db)
    except Exception as exc:
        logger.warning("Notification failed for task_state_changed task=%s: %s", task_id, exc)

    return _to_response(task)


async def confirm_activation(task_id: str, actor, db: AsyncSession) -> TaskResponse:
    if actor.role not in TASK_ACTIVATION_ROLES:
        raise ForbiddenException("Only dispatchers can confirm task activation")
    task = await repository.get_task_by_id(task_id, db)
    if task is None:
        raise NotFoundException(f"Task {task_id} not found")
    if not task.pending_activation:
        raise HTTPException(status_code=400, detail="Task is not pending activation")
    task = await repository.set_pending_activation(task_id, False, db)
    task = await repository.update_task_state(task_id, "active", db)
    return _to_response(task)
