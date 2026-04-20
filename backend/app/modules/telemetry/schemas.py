import math
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

POSITION_SENSOR_TYPES = {"pos_x", "pos_y"}
STANDARD_SENSOR_TYPES = {"engine_temp", "fuel_level", "speed", "payload_weight"}
ALL_SENSOR_TYPES = STANDARD_SENSOR_TYPES | POSITION_SENSOR_TYPES


class IngestTelemetryRequest(BaseModel):
    machine_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: str

    @field_validator("value")
    @classmethod
    def must_be_finite(cls, v):
        if not math.isfinite(v):
            raise ValueError("value must be a finite number")
        return v

    @field_validator("sensor_type")
    @classmethod
    def valid_sensor_type(cls, v):
        if v not in ALL_SENSOR_TYPES:
            raise ValueError(f"sensor_type must be one of {ALL_SENSOR_TYPES}")
        return v


class TelemetryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    machine_id: str
    sensor_type: str
    normalized_value: float
    canonical_unit: str
    timestamp: datetime


class PositionTelemetryResponse(BaseModel):
    """Lightweight response for pos_x/pos_y telemetry — no DB record created."""
    sensor_type: str
    value: float
    machine_id: str
