import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundException
from app.common.roles import OPERATIONAL_NOTIFY_ROLES
from app.modules.machine import repository
from app.modules.machine.conflict_service import detect_and_handle_conflict
from app.modules.machine.schemas import (
    AssignDispatcherRequest,
    CreateMachineRequest,
    MachineResponse,
    UpdateMachineStateRequest,
)
from app.modules.notification.service import NotificationService

logger = logging.getLogger(__name__)

_notification_service = NotificationService()


async def find_all(db: AsyncSession) -> list[MachineResponse]:
    machines = await repository.get_all_machines(db)
    return [MachineResponse.model_validate(m) for m in machines]


async def find_by_id(machine_id: str, db: AsyncSession) -> MachineResponse:
    machine = await repository.get_machine_by_id(machine_id, db)
    if machine is None:
        raise NotFoundException(f"Machine {machine_id} not found")
    return MachineResponse.model_validate(machine)


async def create(
    payload: CreateMachineRequest,
    actor,
    db: AsyncSession,
    event_service,
    notification_service,
) -> MachineResponse:
    machine = await repository.create_machine(payload.name, payload.type, payload.initial_state, db)

    source = "dispatcher" if actor.role == "dispatcher" else "operator"
    await repository.insert_machine_state(
        machine_id=machine.id,
        state=payload.initial_state,
        source=source,
        set_by_user_id=actor.id,
        db=db,
    )

    if event_service is not None:
        try:
            await event_service.emit(
                machine_id=machine.id,
                event_type="MACHINE_STATE_CHANGED",
                payload={"state": payload.initial_state, "source": source},
                db=db,
            )
        except Exception as exc:
            logger.warning("Event emit failed for MACHINE_STATE_CHANGED machine=%s: %s", machine.id, exc)

    return MachineResponse.model_validate(machine)


async def update_state(
    machine_id: str,
    payload: UpdateMachineStateRequest,
    actor,
    db: AsyncSession,
    event_service,
    notification_service,
) -> MachineResponse:
    machine = await repository.get_machine_by_id(machine_id, db)
    if machine is None:
        raise NotFoundException(f"Machine {machine_id} not found")

    previous_state = machine.current_state
    source = "dispatcher" if actor.role == "dispatcher" else "operator"

    await repository.insert_machine_state(
        machine_id=machine_id,
        state=payload.state,
        source=source,
        set_by_user_id=actor.id,
        db=db,
    )

    await detect_and_handle_conflict(machine_id, actor.role, db, event_service, notification_service)

    try:
        await _notification_service.broadcast_to_roles(
            roles=list(OPERATIONAL_NOTIFY_ROLES),
            type_="system",
            name=f"Machine State Changed: {machine.name}",
            desc=f"State: {previous_state} → {payload.state} | By: {actor.role}",
            bigdesc=f"Machine ID: {machine_id}\nType: {machine.type}",
            db=db,
        )
    except Exception as exc:
        logger.warning("Notification failed for machine_state_changed machine=%s: %s", machine_id, exc)

    updated = await repository.get_machine_by_id(machine_id, db)
    return MachineResponse.model_validate(updated)


async def assign_dispatcher(
    machine_id: str,
    payload: AssignDispatcherRequest,
    db: AsyncSession,
) -> None:
    machine = await repository.get_machine_by_id(machine_id, db)
    if machine is None:
        raise NotFoundException(f"Machine {machine_id} not found")
    await repository.assign_dispatcher(machine_id, payload.dispatcher_id, db)


async def resolve_conflict(
    machine_id: str,
    conflict_id: str,
    actor,
    db: AsyncSession,
    event_service,
) -> MachineResponse:
    machine = await repository.get_machine_by_id(machine_id, db)
    if machine is None:
        raise NotFoundException(f"Machine {machine_id} not found")

    await repository.resolve_conflict(conflict_id, actor.id, db)
    await repository.update_machine_conflict(machine_id, False, db)

    if event_service is not None:
        try:
            await event_service.emit(
                machine_id=machine_id,
                event_type="MACHINE_STATE_CHANGED",
                payload={"conflict_resolved": True},
                db=db,
            )
        except Exception as exc:
            logger.warning("Event emit failed for conflict resolution machine=%s: %s", machine_id, exc)

    updated = await repository.get_machine_by_id(machine_id, db)
    return MachineResponse.model_validate(updated)
