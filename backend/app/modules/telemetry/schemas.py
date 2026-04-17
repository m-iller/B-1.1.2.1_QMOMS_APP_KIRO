from pydantic import BaseModel, ConfigDict, field_validator
import math

class IngestTelemetryRequest(BaseModel):
    machine_id: str
    sensor_type: str  # engine_temp|fuel_level|speed|payload_weight
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
        valid = {"engine_temp", "fuel_level", "speed", "payload_weight"}
        if v not in valid:
            raise ValueError(f"sensor_type must be one of {valid}")
        return v

class TelemetryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    machine_id: str
    sensor_type: str
    normalized_value: float
    canonical_unit: str
    timestamp: str
