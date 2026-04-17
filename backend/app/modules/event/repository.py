from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.event.models import Event, Shift


async def insert_event(machine_id, event_type, payload, shift_id, db: AsyncSession) -> Event:
    event = Event(machine_id=machine_id, event_type=event_type, payload=payload, shift_id=shift_id)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def find_all_filtered(machine_id, event_type, shift_id, db: AsyncSession) -> list[Event]:
    q = select(Event)
    if machine_id:
        q = q.where(Event.machine_id == machine_id)
    if event_type:
        q = q.where(Event.event_type == event_type)
    if shift_id:
        q = q.where(Event.shift_id == shift_id)
    result = await db.execute(q.order_by(Event.created_at.desc()))
    return list(result.scalars().all())


async def expire_by_shift_id(shift_id: str, db: AsyncSession) -> None:
    await db.execute(update(Event).where(Event.shift_id == shift_id).values(expired=True))
    await db.commit()


async def get_active_shift(db: AsyncSession) -> Shift | None:
    result = await db.execute(select(Shift).where(Shift.active == True).limit(1))  # noqa: E712
    return result.scalar_one_or_none()


async def get_shift_by_id(shift_id: str, db: AsyncSession) -> Shift | None:
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    return result.scalar_one_or_none()


async def get_all_shifts(db: AsyncSession) -> list[Shift]:
    result = await db.execute(select(Shift).order_by(Shift.start_time.desc()))
    return list(result.scalars().all())


async def create_shift(name: str, start_time: str, db: AsyncSession) -> Shift:
    shift = Shift(name=name, start_time=start_time, active=True)
    db.add(shift)
    await db.commit()
    await db.refresh(shift)
    return shift


async def end_shift(shift_id: str, db: AsyncSession) -> Shift:
    from datetime import datetime, timezone
    shift = await get_shift_by_id(shift_id, db)
    shift.active = False
    shift.end_time = datetime.now(timezone.utc).isoformat()
    await db.commit()
    await db.refresh(shift)
    return shift
