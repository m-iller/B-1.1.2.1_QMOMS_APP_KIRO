from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_roles
from app.modules.zone import service
from app.modules.zone.schemas import (
    AssignMachineRequest,
    CreateZoneRequest,
    UpdateZoneRequest,
    ZoneResponse,
)

router = APIRouter()

try:
    from app.modules.event.service import EventService as _EventService
    _event_service = _EventService()
except (ImportError, Exception):
    _event_service = None


@router.get("", response_model=list[ZoneResponse])
async def list_zones(
    db: AsyncSession = Depends(get_db),
    _actor=Depends(get_current_user),
):
    return await service.find_all(db)


@router.post("", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_zone(
    payload: CreateZoneRequest,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["admin", "dispatcher"])),
):
    return await service.create(payload, db)


@router.get("/{zone_id}", response_model=ZoneResponse)
async def get_zone(
    zone_id: str,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(get_current_user),
):
    return await service.find_by_id(zone_id, db)


@router.patch("/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    zone_id: str,
    payload: UpdateZoneRequest,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["admin", "dispatcher"])),
):
    return await service.update(zone_id, payload, db)


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(
    zone_id: str,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["admin"])),
):
    await service.delete(zone_id, db)


@router.post("/{zone_id}/machines", status_code=status.HTTP_204_NO_CONTENT)
async def assign_machine(
    zone_id: str,
    payload: AssignMachineRequest,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["dispatcher"])),
):
    await service.assign_machine(zone_id, payload, db, _event_service)


@router.get("/{zone_id}/machines")
async def get_machines_in_zone(
    zone_id: str,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(get_current_user),
):
    return await service.get_machines(zone_id, db)
