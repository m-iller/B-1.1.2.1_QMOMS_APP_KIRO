from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.machine.models import Machine, MachineState
from app.modules.report.models import Report
from app.modules.task.models import Task
from app.modules.telemetry.models import Anomaly


async def insert_report(shift_id: str, generated_by: str | None, data: dict, db: AsyncSession) -> Report:
    report = Report(shift_id=shift_id, generated_by=generated_by, data=data)
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def find_all(db: AsyncSession) -> list[Report]:
    result = await db.execute(select(Report).order_by(Report.generated_at.desc()))
    return list(result.scalars().all())


async def find_by_id(report_id: str, db: AsyncSession) -> Report | None:
    result = await db.execute(select(Report).where(Report.id == report_id))
    return result.scalar_one_or_none()


async def get_all_machines(db: AsyncSession) -> list[Machine]:
    result = await db.execute(select(Machine))
    return list(result.scalars().all())


async def count_machine_states_in_range(
    machine_id: str,
    start_time,
    end_time,
    db: AsyncSession,
) -> int:
    query = select(func.count()).where(MachineState.machine_id == machine_id)
    if start_time:
        query = query.where(MachineState.created_at >= start_time)
    if end_time:
        query = query.where(MachineState.created_at <= end_time)
    result = await db.execute(query)
    return result.scalar() or 0


async def count_operating_states_in_range(
    machine_id: str,
    start_time,
    end_time,
    db: AsyncSession,
) -> int:
    query = (
        select(func.count())
        .where(MachineState.machine_id == machine_id)
        .where(MachineState.source == "telemetry")
        .where(MachineState.state == "operating")
    )
    if start_time:
        query = query.where(MachineState.created_at >= start_time)
    if end_time:
        query = query.where(MachineState.created_at <= end_time)
    result = await db.execute(query)
    return result.scalar() or 0


async def count_tasks_by_state(state: str, db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(Task).where(Task.state == state)
    )
    return result.scalar() or 0


async def get_anomaly_counts_by_machine(db: AsyncSession) -> dict[str, int]:
    rows = await db.execute(
        select(Anomaly.machine_id, func.count().label("cnt")).group_by(Anomaly.machine_id)
    )
    return {row.machine_id: row.cnt for row in rows}
