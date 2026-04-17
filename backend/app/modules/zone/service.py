from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ConflictException, NotFoundException
from app.modules.zone import repository
from app.modules.zone.schemas import (
    AssignMachineRequest,
    CreateZoneRequest,
    UpdateZoneRequest,
    ZoneResponse,
)


def _to_response(zone) -> ZoneResponse:
    return ZoneResponse(
        id=str(zone.id),
        name=zone.name,
        description=zone.description,
        created_at=str(zone.created_at),
        updated_at=str(zone.updated_at),
    )


async def find_all(db: AsyncSession) -> list[ZoneResponse]:
    zones = await repository.get_all_zones(db)
    return [_to_response(z) for z in zones]


async def find_by_id(zone_id: str, db: AsyncSession) -> ZoneResponse:
    zone = await repository.get_zone_by_id(zone_id, db)
    if zone is None:
        raise NotFoundException(f"Zone {zone_id} not found")
    return _to_response(zone)


async def create(payload: CreateZoneRequest, db: AsyncSession) -> ZoneResponse:
    zone = await repository.create_zone(payload.name, payload.description, db)
    return _to_response(zone)


async def update(zone_id: str, payload: UpdateZoneRequest, db: AsyncSession) -> ZoneResponse:
    zone = await repository.get_zone_by_id(zone_id, db)
    if zone is None:
        raise NotFoundException(f"Zone {zone_id} not found")
    zone = await repository.update_zone(zone_id, payload.name, payload.description, db)
    return _to_response(zone)


async def delete(zone_id: str, db: AsyncSession) -> None:
    zone = await repository.get_zone_by_id(zone_id, db)
    if zone is None:
        raise NotFoundException(f"Zone {zone_id} not found")
    count = await repository.count_machines_in_zone(zone_id, db)
    if count > 0:
        raise ConflictException(f"Zone {zone_id} has {count} machine(s) assigned")
    await repository.delete_zone(zone_id, db)


async def assign_machine(
    zone_id: str,
    payload: AssignMachineRequest,
    db: AsyncSession,
    event_service=None,
) -> None:
    zone = await repository.get_zone_by_id(zone_id, db)
    if zone is None:
        raise NotFoundException(f"Zone {zone_id} not found")
    await repository.assign_machine_to_zone(payload.machine_id, zone_id, db)
    if event_service is not None:
        await event_service.emit(
            machine_id=payload.machine_id,
            event_type="MACHINE_STATE_CHANGED",
            payload={"zone_id": zone_id},
            db=db,
        )


async def get_machines(zone_id: str, db: AsyncSession) -> list:
    zone = await repository.get_zone_by_id(zone_id, db)
    if zone is None:
        raise NotFoundException(f"Zone {zone_id} not found")
    machines = await repository.get_machines_in_zone(zone_id, db)
    return [
        {
            "id": str(m.id),
            "name": m.name,
            "type": m.type,
            "current_state": m.current_state,
        }
        for m in machines
    ]
