from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundException
from app.modules.event.repository import get_shift_by_id
from app.modules.machine.models import Machine, MachineState
from app.modules.task.models import Task
from app.modules.telemetry.models import Anomaly
from app.modules.report import repository
from app.modules.report.schemas import (
    AnomalyCount,
    GenerateReportRequest,
    MachineUtilization,
    ReportData,
    ReportResponse,
    TaskCounts,
)


async def generate(payload: GenerateReportRequest, actor, db: AsyncSession) -> ReportResponse:
    shift = await get_shift_by_id(payload.shift_id, db)
    if shift is None:
        raise NotFoundException("Shift not found")

    # All machines
    machines_result = await db.execute(select(Machine))
    machines = list(machines_result.scalars().all())

    # Machine utilization per machine within shift time range
    machine_utilization: list[MachineUtilization] = []
    for machine in machines:
        # Base query: machine_states for this machine within shift time range
        base_q = select(func.count()).where(MachineState.machine_id == machine.id)
        if shift.start_time:
            base_q = base_q.where(MachineState.created_at >= shift.start_time)
        if shift.end_time:
            base_q = base_q.where(MachineState.created_at <= shift.end_time)

        total_result = await db.execute(base_q)
        total = total_result.scalar() or 0

        if total > 0:
            operating_q = (
                select(func.count())
                .where(MachineState.machine_id == machine.id)
                .where(MachineState.source == "telemetry")
                .where(MachineState.state == "operating")
            )
            if shift.start_time:
                operating_q = operating_q.where(MachineState.created_at >= shift.start_time)
            if shift.end_time:
                operating_q = operating_q.where(MachineState.created_at <= shift.end_time)

            operating_result = await db.execute(operating_q)
            operating = operating_result.scalar() or 0
            utilization_percent = (operating / total) * 100
        else:
            utilization_percent = 0.0

        machine_utilization.append(
            MachineUtilization(
                machine_id=machine.id,
                machine_name=machine.name,
                utilization_percent=utilization_percent,
            )
        )

    # Task counts by state
    async def _count_tasks(state: str) -> int:
        result = await db.execute(
            select(func.count()).select_from(Task).where(Task.state == state)
        )
        return result.scalar() or 0

    task_counts = TaskCounts(
        pending=await _count_tasks("pending"),
        active=await _count_tasks("active"),
        completed=await _count_tasks("completed"),
        validated=await _count_tasks("validated"),
    )

    # Anomaly counts per machine
    anomaly_rows = await db.execute(
        select(Anomaly.machine_id, func.count().label("cnt")).group_by(Anomaly.machine_id)
    )
    anomaly_map = {row.machine_id: row.cnt for row in anomaly_rows}

    machine_name_map = {m.id: m.name for m in machines}
    anomaly_counts: list[AnomalyCount] = [
        AnomalyCount(
            machine_id=mid,
            machine_name=machine_name_map.get(mid, mid),
            count=cnt,
        )
        for mid, cnt in anomaly_map.items()
    ]

    report_data = ReportData(
        machine_utilization=machine_utilization,
        task_counts=task_counts,
        anomaly_counts=anomaly_counts,
    )

    actor_id = getattr(actor, "id", None)
    report = await repository.insert_report(
        shift_id=payload.shift_id,
        generated_by=actor_id,
        data=report_data.model_dump(),
        db=db,
    )
    return ReportResponse.model_validate(report)


async def find_all(db: AsyncSession) -> list[ReportResponse]:
    reports = await repository.find_all(db)
    return [ReportResponse.model_validate(r) for r in reports]
