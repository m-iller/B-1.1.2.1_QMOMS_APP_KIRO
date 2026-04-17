from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.task.models import HaulCycle

async def get_all_haul_cycles(db: AsyncSession) -> list[HaulCycle]:
    result = await db.execute(select(HaulCycle))
    return list(result.scalars().all())

async def get_haul_cycle_by_id(haul_cycle_id: str, db: AsyncSession) -> HaulCycle | None:
    result = await db.execute(select(HaulCycle).where(HaulCycle.id == haul_cycle_id))
    return result.scalar_one_or_none()

async def create_haul_cycle(machine_id, origin_zone_id, destination_zone_id, payload_tonnes, start_time, db: AsyncSession) -> HaulCycle:
    hc = HaulCycle(machine_id=machine_id, origin_zone_id=origin_zone_id, destination_zone_id=destination_zone_id, payload_tonnes=payload_tonnes, start_time=start_time, status="in_progress")
    db.add(hc)
    await db.commit()
    await db.refresh(hc)
    return hc

async def complete_haul_cycle(haul_cycle_id: str, db: AsyncSession) -> HaulCycle:
    hc = await get_haul_cycle_by_id(haul_cycle_id, db)
    hc.status = "completed"
    hc.immutable = True
    hc.end_time = datetime.now(timezone.utc).isoformat()
    await db.commit()
    await db.refresh(hc)
    return hc
