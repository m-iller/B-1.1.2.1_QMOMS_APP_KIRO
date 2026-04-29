"""
Analytics repository — all DB queries for the dashboard endpoint.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.machine.models import Machine, MachineState, Conflict
from app.modules.task.models import HaulCycle, Task
from app.modules.telemetry.models import TelemetryData


# ---------------------------------------------------------------------------
# Haul cycle queries
# ---------------------------------------------------------------------------

async def get_completed_haul_cycles(db: AsyncSession) -> list[HaulCycle]:
    result = await db.execute(
        select(HaulCycle).where(HaulCycle.status == "completed")
    )
    return list(result.scalars().all())


async def get_haul_cycles_by_destination(db: AsyncSession) -> dict[str, float]:
    """Return total payload tonnes grouped by destination_zone_id."""
    rows = await db.execute(
        select(HaulCycle.destination_zone_id, func.sum(HaulCycle.payload_tonnes))
        .where(HaulCycle.status == "completed")
        .group_by(HaulCycle.destination_zone_id)
    )
    return {row[0]: float(row[1]) for row in rows}


async def get_haul_cycles_by_origin(db: AsyncSession) -> dict[str, float]:
    """Return total payload tonnes grouped by origin_zone_id."""
    rows = await db.execute(
        select(HaulCycle.origin_zone_id, func.sum(HaulCycle.payload_tonnes))
        .where(HaulCycle.status == "completed")
        .group_by(HaulCycle.origin_zone_id)
    )
    return {row[0]: float(row[1]) for row in rows}


# ---------------------------------------------------------------------------
# Machine queries
# ---------------------------------------------------------------------------

async def get_all_machines(db: AsyncSession) -> list[Machine]:
    result = await db.execute(select(Machine))
    return list(result.scalars().all())


async def get_machine_state_counts(db: AsyncSession) -> dict[str, int]:
    """Return count of machines per current_state."""
    rows = await db.execute(
        select(Machine.current_state, func.count()).group_by(Machine.current_state)
    )
    return {row[0]: row[1] for row in rows}


async def get_utilization_per_machine(db: AsyncSession) -> dict[str, float]:
    """
    Compute utilization % per machine as:
    operating_state_count / total_state_count * 100
    """
    total_rows = await db.execute(
        select(MachineState.machine_id, func.count().label("total"))
        .group_by(MachineState.machine_id)
    )
    total_map: dict[str, int] = {row.machine_id: row.total for row in total_rows}

    operating_rows = await db.execute(
        select(MachineState.machine_id, func.count().label("operating"))
        .where(MachineState.state == "operating")
        .group_by(MachineState.machine_id)
    )
    operating_map: dict[str, int] = {row.machine_id: row.operating for row in operating_rows}

    utilization: dict[str, float] = {}
    for machine_id, total in total_map.items():
        operating = operating_map.get(machine_id, 0)
        utilization[machine_id] = (operating / total * 100) if total > 0 else 0.0
    return utilization


async def count_breakdown_events(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(Conflict)
    )
    return result.scalar() or 0


async def get_machines_with_recent_telemetry(
    db: AsyncSession,
    within_minutes: int = 30,
) -> set[str]:
    """Return machine IDs that have sent telemetry in the last N minutes."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=within_minutes)
    rows = await db.execute(
        select(TelemetryData.machine_id)
        .where(TelemetryData.timestamp >= cutoff)
        .distinct()
    )
    return {row[0] for row in rows}


# ---------------------------------------------------------------------------
# Task queries
# ---------------------------------------------------------------------------

async def get_task_counts(db: AsyncSession) -> dict[str, int]:
    rows = await db.execute(
        select(Task.state, func.count()).group_by(Task.state)
    )
    return {row[0]: row[1] for row in rows}


async def count_overdue_tasks(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(func.count())
        .select_from(Task)
        .where(Task.state.notin_(["completed", "validated"]))
        .where(Task.deadline < now)
    )
    return result.scalar() or 0


# ---------------------------------------------------------------------------
# Zone name lookup
# ---------------------------------------------------------------------------

async def get_zone_names(db: AsyncSession) -> dict[str, str]:
    """Return {zone_id: zone_name} map."""
    from app.modules.zone.models import Zone
    rows = await db.execute(select(Zone.id, Zone.name))
    return {row[0]: row[1] for row in rows}
