from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_roles
from app.modules.machine import service
from app.modules.machine.schemas import (
    AssignDispatcherRequest,
    CreateMachineRequest,
    ConflictResponse,
    MachineResponse,
    ResolveConflictRequest,
    UpdateMachineConfigRequest,
    UpdateMachineStateRequest,
)

router = APIRouter()

# Lazy service stubs — real implementations come in Tasks 8 and 11
try:
    from app.modules.event.service import EventService as _EventService
    _event_service = _EventService()
except (ImportError, Exception):
    _event_service = None

try:
    from app.modules.notification.service import NotificationService as _NotificationService
    _notification_service = _NotificationService()
except (ImportError, Exception):
    _notification_service = None


@router.get("", response_model=list[MachineResponse])
async def list_machines(
    db: AsyncSession = Depends(get_db),
    _actor=Depends(get_current_user),
):
    return await service.find_all(db)


@router.post("", response_model=MachineResponse, status_code=201)
async def create_machine(
    payload: CreateMachineRequest,
    db: AsyncSession = Depends(get_db),
    actor=Depends(require_roles(["admin", "dispatcher"])),
):
    return await service.create(payload, actor, db, _event_service, _notification_service)


@router.get("/{machine_id}", response_model=MachineResponse)
async def get_machine(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(get_current_user),
):
    return await service.find_by_id(machine_id, db)


@router.patch("/{machine_id}/state", response_model=MachineResponse)
async def update_machine_state(
    machine_id: str,
    payload: UpdateMachineStateRequest,
    db: AsyncSession = Depends(get_db),
    actor=Depends(require_roles(["dispatcher", "operator", "dev"])),
):
    return await service.update_state(machine_id, payload, actor, db, _event_service, _notification_service)


@router.patch("/{machine_id}/dispatcher", status_code=204)
async def assign_dispatcher(
    machine_id: str,
    payload: AssignDispatcherRequest,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["admin", "dispatcher"])),
):
    await service.assign_dispatcher(machine_id, payload, db)


@router.patch("/{machine_id}/config", response_model=MachineResponse)
async def update_machine_config(
    machine_id: str,
    payload: UpdateMachineConfigRequest,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["admin", "dispatcher", "dev"])),
):
    return await service.update_config(machine_id, payload.description, payload.enabled_sensors, db)


@router.delete("/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_machine(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["admin", "dev"])),
):
    await service.delete(machine_id, db)


@router.get("/{machine_id}/conflicts", response_model=list[ConflictResponse])
async def list_machine_conflicts(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(get_current_user),
):
    from app.modules.machine.repository import get_unresolved_conflicts
    conflicts = await get_unresolved_conflicts(machine_id, db)
    return [
        ConflictResponse(
            id=c.id,
            machine_id=c.machine_id,
            dispatcher_state=c.dispatcher_state,
            operator_state=c.operator_state,
            resolved=c.resolved,
            resolved_by_user_id=c.resolved_by_user_id,
            resolved_at=c.resolved_at,
            created_at=c.created_at,
        )
        for c in conflicts
    ]


@router.post("/{machine_id}/conflicts/{conflict_id}/resolve", response_model=MachineResponse)
async def resolve_conflict(
    machine_id: str,
    conflict_id: str,
    payload: ResolveConflictRequest,
    db: AsyncSession = Depends(get_db),
    actor=Depends(require_roles(["dispatcher", "dev"])),
):
    return await service.resolve_conflict(machine_id, conflict_id, payload.resolution, actor, db, _event_service)
