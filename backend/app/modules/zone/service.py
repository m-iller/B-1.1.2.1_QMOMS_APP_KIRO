import math
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ConflictException, NotFoundException
from app.common.roles import OPERATIONAL_NOTIFY_ROLES
from app.modules.zone import repository
from app.modules.zone.schemas import (
    AssignMachineRequest,
    CreateZoneRequest,
    UpdateZoneRequest,
    ZoneResponse,
)

logger = logging.getLogger(__name__)


def _to_response(zone) -> ZoneResponse:
    return ZoneResponse(
        id=str(zone.id),
        name=zone.name,
        description=zone.description,
        zone_type=zone.zone_type,
        color=zone.color,
        center_lat=zone.center_lat,
        center_lng=zone.center_lng,
        radius_meters=zone.radius_meters,
        created_at=str(zone.created_at),
        updated_at=str(zone.updated_at),
    )


def _haversine_distance_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in meters between two lat/lng points."""
    earth_radius_meters = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return earth_radius_meters * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def find_all(db: AsyncSession) -> list[ZoneResponse]:
    zones = await repository.get_all_zones(db)
    return [_to_response(z) for z in zones]


async def find_by_id(zone_id: str, db: AsyncSession) -> ZoneResponse:
    zone = await repository.get_zone_by_id(zone_id, db)
    if zone is None:
        raise NotFoundException(f"Zone {zone_id} not found")
    return _to_response(zone)


async def create(payload: CreateZoneRequest, db: AsyncSession) -> ZoneResponse:
    zone = await repository.create_zone(
        name=payload.name,
        description=payload.description,
        zone_type=payload.zone_type,
        color=payload.color,
        center_lat=payload.center_lat,
        center_lng=payload.center_lng,
        radius_meters=payload.radius_meters,
        db=db,
    )
    return _to_response(zone)


async def update(zone_id: str, payload: UpdateZoneRequest, db: AsyncSession) -> ZoneResponse:
    zone = await repository.get_zone_by_id(zone_id, db)
    if zone is None:
        raise NotFoundException(f"Zone {zone_id} not found")
    zone = await repository.update_zone(
        zone_id=zone_id,
        name=payload.name,
        description=payload.description,
        zone_type=payload.zone_type,
        color=payload.color,
        center_lat=payload.center_lat,
        center_lng=payload.center_lng,
        radius_meters=payload.radius_meters,
        db=db,
    )
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
            event_type="MACHINE_ENTERED_ZONE",
            payload={"zone_id": zone_id, "zone_name": zone.name},
            db=db,
        )


async def get_machines(zone_id: str, db: AsyncSession) -> list:
    zone = await repository.get_zone_by_id(zone_id, db)
    if zone is None:
        raise NotFoundException(f"Zone {zone_id} not found")
    machines = await repository.get_machines_in_zone(zone_id, db)
    return [
        {"id": str(m.id), "name": m.name, "type": m.type, "current_state": m.current_state}
        for m in machines
    ]


async def check_zone_entry(
    machine_id: str,
    machine_name: str,
    lat: float,
    lng: float,
    db: AsyncSession,
    notification_service=None,
) -> None:
    """
    Check if machine position is inside any zone.
    Sends notification if machine enters a zone with geometry configured.
    """
    zones = await repository.get_all_zones(db)
    for zone in zones:
        if zone.center_lat is None or zone.center_lng is None or zone.radius_meters is None:
            continue
        distance = _haversine_distance_meters(lat, lng, zone.center_lat, zone.center_lng)
        if distance <= zone.radius_meters:
            if notification_service is not None:
                try:
                    from app.modules.auth.repository import get_users_by_roles
                    users = await get_users_by_roles(list(OPERATIONAL_NOTIFY_ROLES), db)
                    from app.modules.notification.service import _build_payload
                    from app.modules.notification import repository as notif_repo
                    payload = _build_payload(
                        name=f"Machine Entered Zone: {zone.name}",
                        desc=f"{machine_name} entered {zone.name} ({zone.zone_type or 'general'})",
                        bigdesc=f"Machine ID: {machine_id}\nZone: {zone.name}\nDistance from center: {distance:.0f}m",
                    )
                    for user in users:
                        await notif_repo.insert_notification(str(user.id), "system", payload, None, db)
                except Exception as exc:
                    logger.warning("Zone entry notification failed machine=%s zone=%s: %s", machine_id, zone.id, exc)
