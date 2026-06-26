from fastapi import APIRouter, Depends, Query, status
from app.common.roles import DISPATCHER_ROLES
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_current_user, get_current_user_optional, get_db, require_roles
from app.modules.task import service, haul_cycle_service
from app.modules.task.schemas import CreateHaulCycleRequest, CreateTaskRequest, HaulCycleResponse, TaskResponse, UpdateTaskRequest

router = APIRouter()

try:
    from app.modules.event.service import EventService as _ES
    _event_service = _ES()
except (ImportError, Exception):
    _event_service = None

@router.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(
    machine_id: str | None = Query(None),
    state: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _actor=Depends(get_current_user_optional),  # Optional auth for simulator
):
    """
    List tasks. Authentication is optional to allow simulator to query tasks.
    """
    return await service.find_all(machine_id, state, db)

@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    payload: CreateTaskRequest,
    db: AsyncSession = Depends(get_db),
    actor=Depends(get_current_user_optional),  # Optional auth for simulator
):
    """
    Create a task. Authentication is optional to allow simulator to create tasks.
    """
    return await service.create(payload, actor, db, _event_service)

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(get_current_user),
):
    return await service.find_by_id(task_id, db)

@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    payload: UpdateTaskRequest,
    db: AsyncSession = Depends(get_db),
    actor=Depends(get_current_user_optional),  # Optional auth for simulator
):
    """
    Update a task. Authentication is optional to allow simulator to update task state.
    """
    return await service.update_state(task_id, payload, actor, db, _event_service)

@router.post("/tasks/{task_id}/confirm-activation", response_model=TaskResponse)
async def confirm_activation(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    actor=Depends(require_roles(["dispatcher"])),
):
    return await service.confirm_activation(task_id, actor, db)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["dispatcher", "admin", "dev"])),
):
    await service.delete(task_id, db)

@router.get("/haul-cycles", response_model=list[HaulCycleResponse])
async def list_haul_cycles(
    db: AsyncSession = Depends(get_db),
    _actor=Depends(get_current_user),
):
    return await haul_cycle_service.find_all(db)

@router.post("/haul-cycles", response_model=HaulCycleResponse, status_code=201)
async def create_haul_cycle(
    payload: CreateHaulCycleRequest,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["dispatcher"])),
):
    return await haul_cycle_service.create(payload, db)

@router.patch("/haul-cycles/{haul_cycle_id}/complete", response_model=HaulCycleResponse)
async def complete_haul_cycle(
    haul_cycle_id: str,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["dispatcher"])),
):
    return await haul_cycle_service.complete(haul_cycle_id, db)
