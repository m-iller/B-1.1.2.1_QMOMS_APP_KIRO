from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.machine.models import Machine
from app.modules.zone.models import Zone


async def get_all_zones(db: AsyncSession) -> list[Zone]:
    result = await db.execute(select(Zone).order_by(Zone.created_at))
    return list(result.scalars().all())


async def get_zone_by_id(zone_id: str, db: AsyncSession) -> Zone | None:
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    return result.scalar_one_or_none()


async def create_zone(name: str, description: str | None, db: AsyncSession) -> Zone:
    zone = Zone(name=name, description=description)
    db.add(zone)
    await db.flush()
    await db.refresh(zone)
    return zone


async def update_zone(
    zone_id: str, name: str | None, description: str | None, db: AsyncSession
) -> Zone:
    values: dict = {}
    if name is not None:
        values["name"] = name
    if description is not None:
        values["description"] = description
    if values:
        values["updated_at"] = func.now()
        await db.execute(update(Zone).where(Zone.id == zone_id).values(**values))
        await db.flush()
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    return result.scalar_one()


async def delete_zone(zone_id: str, db: AsyncSession) -> None:
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one()
    await db.delete(zone)
    await db.flush()


async def count_machines_in_zone(zone_id: str, db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(Machine).where(Machine.current_zone_id == zone_id)
    )
    return result.scalar_one()


async def assign_machine_to_zone(machine_id: str, zone_id: str, db: AsyncSession) -> None:
    await db.execute(
        update(Machine).where(Machine.id == machine_id).values(current_zone_id=zone_id)
    )
    await db.flush()


async def get_machines_in_zone(zone_id: str, db: AsyncSession) -> list[Machine]:
    result = await db.execute(
        select(Machine).where(Machine.current_zone_id == zone_id)
    )
    return list(result.scalars().all())
