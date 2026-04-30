from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.route.models import MachineRoute


async def get_all_routes(db: AsyncSession) -> list[MachineRoute]:
    result = await db.execute(select(MachineRoute).order_by(MachineRoute.created_at))
    return list(result.scalars().all())


async def get_routes_by_machine(machine_id: str, db: AsyncSession) -> list[MachineRoute]:
    result = await db.execute(
        select(MachineRoute).where(MachineRoute.machine_id == machine_id)
    )
    return list(result.scalars().all())


async def get_route_by_id(route_id: str, db: AsyncSession) -> MachineRoute | None:
    result = await db.execute(select(MachineRoute).where(MachineRoute.id == route_id))
    return result.scalar_one_or_none()


async def create_route(
    machine_id: str,
    name: str,
    waypoints: list[dict],
    color: str,
    db: AsyncSession,
) -> MachineRoute:
    route = MachineRoute(machine_id=machine_id, name=name, waypoints=waypoints, color=color)
    db.add(route)
    await db.commit()
    await db.refresh(route)
    return route


async def update_route(
    route_id: str,
    name: str | None,
    waypoints: list[dict] | None,
    color: str | None,
    db: AsyncSession,
) -> MachineRoute:
    route = await get_route_by_id(route_id, db)
    if name is not None:
        route.name = name
    if waypoints is not None:
        route.waypoints = waypoints
    if color is not None:
        route.color = color
    route.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(route)
    return route


async def delete_route(route_id: str, db: AsyncSession) -> None:
    route = await get_route_by_id(route_id, db)
    if route is not None:
        await db.delete(route)
        await db.commit()
