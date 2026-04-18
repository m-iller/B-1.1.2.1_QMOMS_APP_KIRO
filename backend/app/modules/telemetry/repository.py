from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.telemetry.models import Anomaly, TelemetryData


async def insert_telemetry(
    machine_id: str,
    sensor_type: str,
    normalized_value: float,
    canonical_unit: str,
    timestamp: str,
    db: AsyncSession,
) -> TelemetryData:
    # Use raw INSERT RETURNING to avoid refresh issues with TimescaleDB composite PK
    result = await db.execute(
        text("""
            INSERT INTO telemetry_data (machine_id, sensor_type, normalized_value, canonical_unit, timestamp)
            VALUES (:machine_id, :sensor_type, :normalized_value, :canonical_unit, :timestamp::timestamptz)
            RETURNING id, machine_id, sensor_type, normalized_value, canonical_unit, timestamp
        """),
        {
            "machine_id": machine_id,
            "sensor_type": sensor_type,
            "normalized_value": normalized_value,
            "canonical_unit": canonical_unit,
            "timestamp": timestamp,
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
    q = """
        SELECT id, machine_id, sensor_type, normalized_value, canonical_unit, timestamp
        FROM telemetry_data
        WHERE machine_id = :machine_id
          AND timestamp >= :from_dt::timestamptz
          AND timestamp <= :to_dt::timestamptz
    """
    params: dict = {"machine_id": machine_id, "from_dt": from_dt, "to_dt": to_dt}
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
