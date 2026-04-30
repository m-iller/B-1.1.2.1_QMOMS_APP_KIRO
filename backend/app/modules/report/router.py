from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_roles
from app.modules.report import service
from app.modules.report.schemas import GenerateReportRequest, ReportResponse

router = APIRouter()

_ALLOWED_ROLES = ["manager", "dispatcher", "admin", "owner"]


@router.get("", response_model=list[ReportResponse])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(_ALLOWED_ROLES)),
):
    return await service.find_all(db)


@router.post("/generate", response_model=ReportResponse, status_code=201)
async def generate_report(
    payload: GenerateReportRequest,
    db: AsyncSession = Depends(get_db),
    actor=Depends(require_roles(_ALLOWED_ROLES)),
):
    return await service.generate(payload, actor, db)


@router.get("/daily")
async def get_daily_report(
    date: str,  # YYYY-MM-DD
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(_ALLOWED_ROLES)),
):
    """
    Returns all data needed for a dispatcher daily report for the given date.
    date: ISO date string e.g. 2026-04-30
    """
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select, func
    from app.modules.machine.models import Machine, MachineState
    from app.modules.task.models import Task
    from app.modules.notification.models import Notification
    from app.modules.task.models import HaulCycle

    try:
        day_start = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    day_end = day_start + timedelta(days=1)

    # Machines
    machines_result = await db.execute(select(Machine))
    machines = list(machines_result.scalars().all())

    # Machine utilization for the day
    machine_stats = []
    for m in machines:
        total_q = select(func.count()).where(
            MachineState.machine_id == m.id,
            MachineState.created_at >= day_start,
            MachineState.created_at < day_end,
        )
        operating_q = select(func.count()).where(
            MachineState.machine_id == m.id,
            MachineState.state == "operating",
            MachineState.created_at >= day_start,
            MachineState.created_at < day_end,
        )
        total = (await db.execute(total_q)).scalar() or 0
        operating = (await db.execute(operating_q)).scalar() or 0
        utilization = round((operating / total * 100) if total > 0 else 0.0, 1)
        machine_stats.append({
            "id": m.id,
            "name": m.name,
            "type": m.type,
            "current_state": m.current_state,
            "utilization_pct": utilization,
            "state_changes": total,
        })

    # Haul cycles for the day
    haul_q = select(HaulCycle).where(
        HaulCycle.created_at >= day_start,
        HaulCycle.created_at < day_end,
    )
    haul_cycles = list((await db.execute(haul_q)).scalars().all())
    total_tonnes = sum(hc.payload_tonnes for hc in haul_cycles)
    completed_hauls = [hc for hc in haul_cycles if hc.status == "completed"]

    # Tasks for the day
    tasks_q = select(Task).where(
        Task.created_at >= day_start,
        Task.created_at < day_end,
    )
    tasks = list((await db.execute(tasks_q)).scalars().all())
    task_summary = {
        "total": len(tasks),
        "completed": sum(1 for t in tasks if t.state in ("completed", "validated")),
        "pending": sum(1 for t in tasks if t.state == "pending"),
        "active": sum(1 for t in tasks if t.state == "active"),
        "overdue": sum(1 for t in tasks if t.state not in ("completed", "validated") and t.deadline < day_end),
    }

    # Notifications for the day
    notif_q = select(Notification).where(
        Notification.created_at >= day_start,
        Notification.created_at < day_end,
    ).order_by(Notification.created_at.desc()).limit(50)
    notifications = list((await db.execute(notif_q)).scalars().all())
    notif_list = [
        {
            "type": n.type,
            "payload": n.payload,
            "created_at": n.created_at.isoformat() if hasattr(n.created_at, 'isoformat') else str(n.created_at),
        }
        for n in notifications
    ]

    return {
        "date": date,
        "machines": machine_stats,
        "haul_cycles": {
            "total": len(haul_cycles),
            "completed": len(completed_hauls),
            "total_tonnes": round(total_tonnes, 2),
        },
        "tasks": task_summary,
        "notifications": notif_list,
        "active_machines": sum(1 for m in machines if m.current_state == "operating"),
        "total_machines": len(machines),
    }
