import logging

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.machine.repository import get_machine_by_id, insert_machine_state, update_position
from app.modules.telemetry import repository
from app.modules.telemetry.normalizer import normalize, CANONICAL_UNITS
from app.modules.telemetry.thresholds import exceeds_threshold, derive_machine_state, THRESHOLDS
from app.modules.telemetry.schemas import (
    IngestTelemetryRequest,
    PositionTelemetryResponse,
    TelemetryResponse,
    POSITION_SENSOR_TYPES,
)

logger = logging.getLogger(__name__)


async def ingest(
    payload: IngestTelemetryRequest,
    db: AsyncSession,
    event_service=None,
    notification_service=None,
):
    machine = await get_machine_by_id(payload.machine_id, db)
    if machine is None:
        raise HTTPException(status_code=404, detail=f"Machine {payload.machine_id} not found")

    # Position sensors update machine record directly — bypass normalization/anomaly pipeline
    if payload.sensor_type in POSITION_SENSOR_TYPES:
        axis = "x" if payload.sensor_type == "pos_x" else "y"
        await update_position(payload.machine_id, axis, payload.value, db)

        # Check zone entry when we have both coordinates (pos_y = lat)
        if payload.sensor_type == "pos_y":
            try:
                from app.modules.zone.service import check_zone_entry
                await check_zone_entry(
                    machine_id=payload.machine_id,
                    machine_name=machine.name,
                    lat=payload.value,
                    lng=machine.pos_x or 0.0,
                    db=db,
                    notification_service=notification_service,
                )
            except Exception as exc:
                logger.warning("Zone entry check failed machine=%s: %s", payload.machine_id, exc)

        return PositionTelemetryResponse(
            sensor_type=payload.sensor_type,
            value=payload.value,
            machine_id=payload.machine_id,
        )

    # Normalize value to canonical unit
    try:
        normalized_value = normalize(payload.sensor_type, payload.value, payload.unit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    canonical_unit = CANONICAL_UNITS[payload.sensor_type]

    record = await repository.insert_telemetry(
        machine_id=payload.machine_id,
        sensor_type=payload.sensor_type,
        normalized_value=normalized_value,
        canonical_unit=canonical_unit,
        timestamp=payload.timestamp,
        db=db,
    )

    # Anomaly detection and alerting
    if exceeds_threshold(payload.sensor_type, normalized_value):
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
                    payload={
                        "sensor_type": payload.sensor_type,
                        "value": normalized_value,
                        "threshold": threshold,
                    },
                    db=db,
                )
            except Exception as exc:
                logger.warning(
                    "Event emit failed for ALERT_TRIGGERED machine=%s sensor=%s: %s",
                    payload.machine_id, payload.sensor_type, exc,
                )

        if notification_service and machine.assigned_dispatcher_id:
            try:
                await notification_service.create(
                    user_id=machine.assigned_dispatcher_id,
                    type_="alert",
                    payload={
                        "machine_id": payload.machine_id,
                        "sensor_type": payload.sensor_type,
                        "value": normalized_value,
                    },
                    db=db,
                )
            except Exception as exc:
                logger.warning(
                    "Notification failed for alert machine=%s sensor=%s: %s",
                    payload.machine_id, payload.sensor_type, exc,
                )

    # Derive and record telemetry-based machine state
    try:
        latest_readings = await repository.get_latest_by_machine(payload.machine_id, db)
        readings = {r.sensor_type: r.normalized_value for r in latest_readings}
        readings[payload.sensor_type] = normalized_value
        derived_state = derive_machine_state(readings)
        if derived_state:
            await insert_machine_state(
                machine_id=payload.machine_id,
                state=derived_state,
                source="telemetry",
                set_by_user_id=None,
                db=db,
            )
    except Exception as exc:
        logger.warning(
            "Failed to derive machine state for machine=%s: %s",
            payload.machine_id, exc,
        )

    return TelemetryResponse.model_validate(record)


async def get_latest_by_machine(machine_id: str, db: AsyncSession) -> list[TelemetryResponse]:
    records = await repository.get_latest_by_machine(machine_id, db)
    return [TelemetryResponse.model_validate(r) for r in records]


async def get_history(
    machine_id: str,
    from_dt: str,
    to_dt: str,
    sensor_type: str | None,
    db: AsyncSession,
) -> list[TelemetryResponse]:
    records = await repository.get_history(machine_id, from_dt, to_dt, sensor_type, db)
    return [TelemetryResponse.model_validate(r) for r in records]
