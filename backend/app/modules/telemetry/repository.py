from datetime import datetime, timezone
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.telemetry.models import TelemetryData, Anomaly

async def insert_telemetry(machine_id, sensor_type, normalized_value, canonical_unit, timestamp, db: AsyncSession) -> TelemetryData:
    record = TelemetryData(
        machine_id=machine_id,
        sensor_type=sensor_type,
        normalized_value=normalized_value,
        canonical_unit=canonical_unit,
        timestamp=timestamp,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record

async def insert_anomaly(machine_id, telemetry_id, sensor_type, value, threshold, db: AsyncSession) -> Anomaly:
    anomaly = Anomaly(
        machine_id=machine_id,
        telemetry_id=telemetry_id,
        sensor_type=sensor_type,
        value=value,
        threshold=threshold,
    )
    db.add(anomaly)
    await db.commit()
    await db.refresh(anomaly)
    return anomaly

async def get_latest_by_machine(machine_id: str, db: AsyncSession) -> list[TelemetryData]:
    # Get latest record per sensor_type using DISTINCT ON
    result = await db.execute(
        text("""
            SELECT DISTINCT ON (sensor_type) id, machine_id, sensor_type, normalized_value, canonical_unit, timestamp
            FROM telemetry_data
            WHERE machine_id = :machine_id
            ORDER BY sensor_type, timestamp DESC
        """),
        {"machine_id": machine_id},
    )
    rows = result.mappings().all()
    return [TelemetryData(**dict(r)) for r in rows]

async def get_history(machine_id: str, from_dt: str, to_dt: str, sensor_type: str | None, db: AsyncSession) -> list[TelemetryData]:
    q = "SELECT id, machine_id, sensor_type, normalized_value, canonical_unit, timestamp FROM telemetry_data WHERE machine_id = :machine_id AND timestamp >= :from_dt AND timestamp <= :to_dt"
    params = {"machine_id": machine_id, "from_dt": from_dt, "to_dt": to_dt}
    if sensor_type:
        q += " AND sensor_type = :sensor_type"
        params["sensor_type"] = sensor_type
    q += " ORDER BY timestamp DESC"
    result = await db.execute(text(q), params)
    rows = result.mappings().all()
    return [TelemetryData(**dict(r)) for r in rows]
