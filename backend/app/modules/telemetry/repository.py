from datetime import datetime, timezone
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.telemetry.models import Anomaly, TelemetryData


def _parse_timestamp(ts: str) -> datetime:
    """Parse ISO8601 string to timezone-aware datetime for asyncpg."""
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


async def insert_telemetry(
    machine_id: str,
    sensor_type: str,
    normalized_value: float,
    canonical_unit: str,
    timestamp: str,
    db: AsyncSession,
) -> TelemetryData:
    ts_dt = _parse_timestamp(timestamp)
    result = await db.execute(
        text("""
            INSERT INTO telemetry_data (machine_id, sensor_type, normalized_value, canonical_unit, timestamp)
            VALUES (:machine_id, :sensor_type, :normalized_value, :canonical_unit, :timestamp)
            RETURNING id, machine_id, sensor_type, normalized_value, canonical_unit, timestamp
        """),
        {
            "machine_id": machine_id,
            "sensor_type": sensor_type,
            "normalized_value": normalized_value,
            "canonical_unit": canonical_unit,
            "timestamp": ts_dt,
        },
    )
    await db.commit()
    row = result.mappings().one()
    record = TelemetryData()
    record.id = str(row["id"])
    record.machine_id = str(row["machine_id"])
    record.sensor_type = row["sensor_type"]
    record.normalized_value = row["normalized_value"]
    record.canonical_unit = row["canonical_unit"]
    record.timestamp = row["timestamp"]
    return record


async def insert_anomaly(
    machine_id: str,
    telemetry_id: str,
    sensor_type: str,
    value: float,
    threshold: float,
    db: AsyncSession,
) -> Anomaly:
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
    result = await db.execute(
        text("""
            SELECT DISTINCT ON (sensor_type)
                id, machine_id, sensor_type, normalized_value, canonical_unit, timestamp
            FROM telemetry_data
            WHERE machine_id = :machine_id
            ORDER BY sensor_type, timestamp DESC
        """),
        {"machine_id": machine_id},
    )
    rows = result.mappings().all()
    records = []
    for r in rows:
        rec = TelemetryData()
        rec.id = str(r["id"])
        rec.machine_id = str(r["machine_id"])
        rec.sensor_type = r["sensor_type"]
        rec.normalized_value = r["normalized_value"]
        rec.canonical_unit = r["canonical_unit"]
        rec.timestamp = r["timestamp"]
        records.append(rec)
    return records


async def get_history(
    machine_id: str,
    from_dt: str,
    to_dt: str,
    sensor_type: str | None,
    db: AsyncSession,
) -> list[TelemetryData]:
    from_dt_parsed = _parse_timestamp(from_dt)
    to_dt_parsed = _parse_timestamp(to_dt)
    q = """
        SELECT id, machine_id, sensor_type, normalized_value, canonical_unit, timestamp
        FROM telemetry_data
        WHERE machine_id = :machine_id
          AND timestamp >= :from_dt
          AND timestamp <= :to_dt
    """
    params: dict = {"machine_id": machine_id, "from_dt": from_dt_parsed, "to_dt": to_dt_parsed}
    if sensor_type:
        q += " AND sensor_type = :sensor_type"
        params["sensor_type"] = sensor_type
    q += " ORDER BY timestamp DESC"
    result = await db.execute(text(q), params)
    rows = result.mappings().all()
    records = []
    for r in rows:
        rec = TelemetryData()
        rec.id = str(r["id"])
        rec.machine_id = str(r["machine_id"])
        rec.sensor_type = r["sensor_type"]
        rec.normalized_value = r["normalized_value"]
        rec.canonical_unit = r["canonical_unit"]
        rec.timestamp = r["timestamp"]
        records.append(rec)
    return records
