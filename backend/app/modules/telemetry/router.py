from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_current_user, get_db, require_roles
from app.modules.telemetry.schemas import IngestTelemetryRequest, TelemetryResponse
from app.modules.telemetry import service

router = APIRouter()

try:
    from app.modules.event.service import EventService as _ES
    _event_service = _ES()
except (ImportError, Exception):
    _event_service = None

try:
    from app.modules.notification.service import NotificationService as _NS
    _notification_service = _NS()
except (ImportError, Exception):
    _notification_service = None

@router.post("", response_model=TelemetryResponse, status_code=201)
async def ingest_telemetry(
    payload: IngestTelemetryRequest,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(get_current_user),
):
    return await service.ingest(payload, db, _event_service, _notification_service)

@router.get("/{machine_id}/latest", response_model=list[TelemetryResponse])
async def get_latest(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(get_current_user),
):
    return await service.get_latest_by_machine(machine_id, db)

@router.get("/{machine_id}/history", response_model=list[TelemetryResponse])
async def get_history(
    machine_id: str,
    from_dt: str = Query(..., alias="from"),
    to_dt: str = Query(..., alias="to"),
    sensor_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["mechanic", "dispatcher", "admin"])),
):
    return await service.get_history(machine_id, from_dt, to_dt, sensor_type, db)
