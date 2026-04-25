from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import NotFoundException
from app.modules.event.repository import get_shift_by_id
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

    machines = await repository.get_all_machines(db)
    machine_name_map = {m.id: m.name for m in machines}

    machine_utilization: list[MachineUtilization] = []
    for machine in machines:
        total_states = await repository.count_machine_states_in_range(
            machine.id, shift.start_time, shift.end_time, db
        )
        if total_states > 0:
            operating_states = await repository.count_operating_states_in_range(
                machine.id, shift.start_time, shift.end_time, db
            )
            utilization_percent = (operating_states / total_states) * 100
        else:
            utilization_percent = 0.0

        machine_utilization.append(
            MachineUtilization(
                machine_id=machine.id,
                machine_name=machine.name,
                utilization_percent=utilization_percent,
            )
        )

    task_counts = TaskCounts(
        pending=await repository.count_tasks_by_state("pending", db),
        active=await repository.count_tasks_by_state("active", db),
        completed=await repository.count_tasks_by_state("completed", db),
        validated=await repository.count_tasks_by_state("validated", db),
    )

    anomaly_map = await repository.get_anomaly_counts_by_machine(db)
    anomaly_counts: list[AnomalyCount] = [
        AnomalyCount(
            machine_id=machine_id,
            machine_name=machine_name_map.get(machine_id, machine_id),
            count=count,
        )
        for machine_id, count in anomaly_map.items()
    ]

    report_data = ReportData(
        machine_utilization=machine_utilization,
        task_counts=task_counts,
        anomaly_counts=anomaly_counts,
    )

    report = await repository.insert_report(
        shift_id=payload.shift_id,
        generated_by=getattr(actor, "id", None),
        data=report_data.model_dump(),
        db=db,
    )
    return ReportResponse.model_validate(report)


async def find_all(db: AsyncSession) -> list[ReportResponse]:
    reports = await repository.find_all(db)
    return [ReportResponse.model_validate(r) for r in reports]
