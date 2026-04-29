from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.machine.models import Conflict, Machine, MachineState


async def get_all_machines(db: AsyncSession) -> list[Machine]:
    result = await db.execute(select(Machine))
    return list(result.scalars().all())


async def get_machine_by_id(machine_id: str, db: AsyncSession) -> Machine | None:
    result = await db.execute(select(Machine).where(Machine.id == machine_id))
    return result.scalar_one_or_none()


async def create_machine(name: str, type_: str, initial_state: str, db: AsyncSession) -> Machine:
    machine = Machine(name=name, type=type_, current_state=initial_state)
    db.add(machine)
    await db.commit()
    await db.refresh(machine)
    return machine


async def update_machine_state(machine_id: str, state: str, db: AsyncSession) -> Machine:
    machine = await get_machine_by_id(machine_id, db)
    machine.current_state = state
    await db.commit()
    await db.refresh(machine)
    return machine


async def update_machine_conflict(machine_id: str, conflict_active: bool, db: AsyncSession) -> None:
    machine = await get_machine_by_id(machine_id, db)
    machine.conflict_active = conflict_active
    await db.commit()


async def assign_dispatcher(machine_id: str, dispatcher_id: str, db: AsyncSession) -> None:
    machine = await get_machine_by_id(machine_id, db)
    machine.assigned_dispatcher_id = dispatcher_id
    await db.commit()


async def update_machine_position(machine_id: str, pos_x: float, pos_y: float, db: AsyncSession) -> None:
    machine = await get_machine_by_id(machine_id, db)
    machine.pos_x = pos_x
    machine.pos_y = pos_y
    await db.commit()


async def update_position(
    machine_id: str,
    axis: str,  # "x" or "y"
    value: float,
    db: AsyncSession,
) -> None:
    """Update a single position axis (pos_x or pos_y) on a machine record."""
    machine = await get_machine_by_id(machine_id, db)
    if axis == "x":
        machine.pos_x = value
    else:
        machine.pos_y = value
    await db.commit()


async def get_latest_machine_state_by_source(
    machine_id: str, source: str, db: AsyncSession
) -> MachineState | None:
    result = await db.execute(
        select(MachineState)
        .where(MachineState.machine_id == machine_id, MachineState.source == source)
        .order_by(MachineState.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def insert_machine_state(
    machine_id: str, state: str, source: str, set_by_user_id: str | None, db: AsyncSession
) -> MachineState:
    ms = MachineState(
        machine_id=machine_id,
        state=state,
        source=source,
        set_by_user_id=set_by_user_id,
    )
    db.add(ms)
    await db.commit()
    await db.refresh(ms)
    return ms


async def get_active_conflict(machine_id: str, db: AsyncSession) -> Conflict | None:
    result = await db.execute(
        select(Conflict).where(
            Conflict.machine_id == machine_id,
            Conflict.resolved == False,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def insert_conflict(
    machine_id: str, dispatcher_state: str, operator_state: str, db: AsyncSession
) -> Conflict:
    conflict = Conflict(
        machine_id=machine_id,
        dispatcher_state=dispatcher_state,
        operator_state=operator_state,
    )
    db.add(conflict)
    await db.commit()
    await db.refresh(conflict)
    return conflict


async def resolve_conflict(conflict_id: str, resolved_by_user_id: str, db: AsyncSession) -> Conflict:
    result = await db.execute(select(Conflict).where(Conflict.id == conflict_id))
    conflict = result.scalar_one_or_none()
    conflict.resolved = True
    conflict.resolved_by_user_id = resolved_by_user_id
    conflict.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(conflict)
    return conflict

async def get_unresolved_conflicts(machine_id: str, db: AsyncSession) -> list[Conflict]:
    result = await db.execute(
        select(Conflict)
        .where(Conflict.machine_id == machine_id, Conflict.resolved == False)  # noqa: E712
        .order_by(Conflict.created_at.desc())
    )
    return list(result.scalars().all())
