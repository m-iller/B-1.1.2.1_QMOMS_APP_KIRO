from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.telemetry import repository
from app.modules.telemetry.normalizer import normalize, CANONICAL_UNITS
from app.modules.telemetry.thresholds import exceeds_threshold, derive_machine_state
from app.modules.telemetry.schemas import IngestTelemetryRequest, TelemetryResponse

async def ingest(payload: IngestTelemetryRequest, db: AsyncSession, event_service=None, notification_service=None) -> TelemetryResponse:
    # Validate machine exists
    from app.modules.machine.repository import get_machine_by_id, insert_machine_state
    machine = await get_machine_by_id(payload.machine_id, db)
    if machine is None:
        raise HTTPException(status_code=404, detail=f"Machine {payload.machine_id} not found")

    # Normalize
    try:
        normalized_value = normalize(payload.sensor_type, payload.value, payload.unit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    canonical_unit = CANONICAL_UNITS[payload.sensor_type]

    # Persist normalized record
    record = await repository.insert_telemetry(
        machine_id=payload.machine_id,
        sensor_type=payload.sensor_type,
        normalized_value=normalized_value,
        canonical_unit=canonical_unit,
        timestamp=payload.timestamp,
        db=db,
    )

    # Anomaly detection
    if exceeds_threshold(payload.sensor_type, normalized_value):
        from app.modules.telemetry.thresholds import THRESHOLDS
        threshold = THRESHOLDS[payload.sensor_type]
        await repository.insert_anomaly(
            machine_id=payload.machine_id,
            telemetry_id=record.id,
            sensor_type=payload.sensor_type,
            value=normalized_value,
            threshold=threshold,
            db=db,
        )
        if event_service:
            try:
                await event_service.emit(
                    machine_id=payload.machine_id,
                    event_type="ALERT_TRIGGERED",
                    payload={"sensor_type": payload.sensor_type, "value": normalized_value, "threshold": threshold},
                    db=db,
                )
            except Exception:
                pass
        if notification_service and machine.assigned_dispatcher_id:
            try:
                await notification_service.create(
                    user_id=machine.assigned_dispatcher_id,
                    type_="alert",
                    payload={"machine_id": payload.machine_id, "sensor_type": payload.sensor_type, "value": normalized_value},
                    db=db,
                )
            except Exception:
                pass

    # Derive and record telemetry-based machine state
    try:
        latest = await repository.get_latest_by_machine(payload.machine_id, db)
        readings = {r.sensor_type: r.normalized_value for r in latest}
        readings[payload.sensor_type] = normalized_value  # include current reading
        derived_state = derive_machine_state(readings)
        if derived_state:
            await insert_machine_state(
                machine_id=payload.machine_id,
                state=derived_state,
                source="telemetry",
                set_by_user_id=None,
                db=db,
            )
    except Exception:
        pass

    return TelemetryResponse.model_validate(record)

async def get_latest_by_machine(machine_id: str, db: AsyncSession) -> list[TelemetryResponse]:
    records = await repository.get_latest_by_machine(machine_id, db)
    return [TelemetryResponse.model_validate(r) for r in records]

async def get_history(machine_id: str, from_dt: str, to_dt: str, sensor_type: str | None, db: AsyncSession) -> list[TelemetryResponse]:
    records = await repository.get_history(machine_id, from_dt, to_dt, sensor_type, db)
    return [TelemetryResponse.model_validate(r) for r in records]
