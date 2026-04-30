import math
import logging
from collections import defaultdict

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

# In-memory tracking: {machine_id: set(zone_id)} — zones the machine is currently inside
# This prevents repeated enter notifications and enables leave notifications.
# Resets on server restart (acceptable — simulator will re-trigger on next position update).
_machine_zone_membership: dict[str, set[str]] = defaultdict(set)


def _to_response(zone) -> ZoneResponse:
    return ZoneResponse(
        id=str(zone.id),
        name=zone.name,
        description=zone.description,
        zone_type=zone.zone_type,
        color=zone.color,
        shape=zone.shape or "circle",
        center_lat=zone.center_lat,
        center_lng=zone.center_lng,
        radius_meters=zone.radius_meters,
        polygon_points=zone.polygon_points,
        created_at=str(zone.created_at),
        updated_at=str(zone.updated_at),
    )


def _haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _point_in_polygon(lat: float, lng: float, points: list[dict]) -> bool:
    """Ray-casting algorithm for point-in-polygon test."""
    n = len(points)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = points[i]["lng"], points[i]["lat"]
        xj, yj = points[j]["lng"], points[j]["lat"]
        if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _machine_in_zone(lat: float, lng: float, zone) -> bool:
    shape = zone.shape or "circle"
    if shape == "circle":
        if zone.center_lat is None or zone.center_lng is None or zone.radius_meters is None:
            return False
        return _haversine_meters(lat, lng, zone.center_lat, zone.center_lng) <= zone.radius_meters
    elif shape in ("rectangle", "polygon"):
        points = zone.polygon_points
        if not points or len(points) < 3:
            return False
        return _point_in_polygon(lat, lng, points)
    return False


async def find_all(db: AsyncSession) -> list[ZoneResponse]:
    zones = await repository.get_all_zones(db)
    return [_to_response(z) for z in zones]


async def find_by_id(zone_id: str, db: AsyncSession) -> ZoneResponse:
    zone = await repository.get_zone_by_id(zone_id, db)
    if zone is None:
        raise NotFoundException(f"Zone {zone_id} not found")
    return _to_response(zone)


async def create(payload: CreateZoneRequest, db: AsyncSession) -> ZoneResponse:
    polygon_points = [p.model_dump() for p in payload.polygon_points] if payload.polygon_points else None
    zone = await repository.create_zone(
        name=payload.name,
        description=payload.description,
        zone_type=payload.zone_type,
        color=payload.color,
        shape=payload.shape,
        center_lat=payload.center_lat,
        center_lng=payload.center_lng,
        radius_meters=payload.radius_meters,
        polygon_points=polygon_points,
        db=db,
    )
    return _to_response(zone)


async def update(zone_id: str, payload: UpdateZoneRequest, db: AsyncSession) -> ZoneResponse:
    zone = await repository.get_zone_by_id(zone_id, db)
    if zone is None:
        raise NotFoundException(f"Zone {zone_id} not found")
    polygon_points = [p.model_dump() for p in payload.polygon_points] if payload.polygon_points else None
    zone = await repository.update_zone(
        zone_id=zone_id,
        name=payload.name,
        description=payload.description,
        zone_type=payload.zone_type,
        color=payload.color,
        shape=payload.shape,
        center_lat=payload.center_lat,
        center_lng=payload.center_lng,
        radius_meters=payload.radius_meters,
        polygon_points=polygon_points,
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


async def assign_machine(zone_id: str, payload: AssignMachineRequest, db: AsyncSession, event_service=None) -> None:
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
    return [{"id": str(m.id), "name": m.name, "type": m.type, "current_state": m.current_state} for m in machines]


async def check_zone_entry(machine_id: str, machine_name: str, lat: float, lng: float, db: AsyncSession, notification_service=None) -> None:
    """
    Check zone membership for a machine position update.
    - Fires ENTER notification only on first entry (not while already inside).
    - Fires LEAVE notification when machine exits a zone it was previously in.
    """
    zones = await repository.get_all_zones(db)
    currently_inside: set[str] = set()

    for zone in zones:
        if _machine_in_zone(lat, lng, zone):
            currently_inside.add(zone.id)

    previously_inside = _machine_zone_membership[machine_id]

    entered_zones = currently_inside - previously_inside
    left_zones = previously_inside - currently_inside

    # Update membership state
    _machine_zone_membership[machine_id] = currently_inside

    if not notification_service:
        return

    zone_map = {z.id: z for z in zones}

    for zone_id in entered_zones:
        zone = zone_map.get(zone_id)
        if zone is None:
            continue
        try:
            from app.modules.auth.repository import get_users_by_roles
            from app.modules.notification.service import _build_payload
            from app.modules.notification import repository as notif_repo
            users = await get_users_by_roles(list(OPERATIONAL_NOTIFY_ROLES), db)
            payload = _build_payload(
                name=f"Machine Entered Zone: {zone.name}",
                desc=f"{machine_name} entered {zone.name} ({zone.zone_type or 'general'})",
                bigdesc=f"Machine ID: {machine_id}\nZone: {zone.name}",
            )
            for user in users:
                await notif_repo.insert_notification(str(user.id), "system", payload, None, db)
        except Exception as exc:
            logger.warning("Zone enter notification failed machine=%s zone=%s: %s", machine_id, zone_id, exc)

    for zone_id in left_zones:
        zone = zone_map.get(zone_id)
        if zone is None:
            continue
        try:
            from app.modules.auth.repository import get_users_by_roles
            from app.modules.notification.service import _build_payload
            from app.modules.notification import repository as notif_repo
            users = await get_users_by_roles(list(OPERATIONAL_NOTIFY_ROLES), db)
            payload = _build_payload(
                name=f"Machine Left Zone: {zone.name}",
                desc=f"{machine_name} left {zone.name} ({zone.zone_type or 'general'})",
                bigdesc=f"Machine ID: {machine_id}\nZone: {zone.name}",
            )
            for user in users:
                await notif_repo.insert_notification(str(user.id), "system", payload, None, db)
        except Exception as exc:
            logger.warning("Zone leave notification failed machine=%s zone=%s: %s", machine_id, zone_id, exc)
