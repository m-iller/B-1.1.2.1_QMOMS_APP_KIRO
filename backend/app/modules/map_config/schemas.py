import json
from pydantic import BaseModel, field_validator


class AntennaDefinition(BaseModel):
    name: str
    lat: float
    lng: float


class MapConfigRequest(BaseModel):
    center_lat: float
    center_lng: float
    default_zoom: int
    antennas: list[AntennaDefinition]

    @field_validator("default_zoom")
    @classmethod
    def valid_zoom(cls, v):
        if not (1 <= v <= 20):
            raise ValueError("default_zoom must be between 1 and 20")
        return v

    @field_validator("antennas")
    @classmethod
    def at_least_one_antenna(cls, v):
        if len(v) < 1:
            raise ValueError("At least one antenna is required")
        return v


class MapConfigResponse(BaseModel):
    center_lat: float
    center_lng: float
    default_zoom: int
    antennas: list[AntennaDefinition]
