from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ZonePoint(BaseModel):
    lat: float
    lng: float


class CreateZoneRequest(BaseModel):
    name: str
    description: Optional[str] = None
    zone_type: Optional[str] = None
    color: Optional[str] = None
    shape: str = "circle"                        # circle | rectangle | polygon
    center_lat: Optional[float] = None           # circle only
    center_lng: Optional[float] = None           # circle only
    radius_meters: float = 200.0                 # circle only
    polygon_points: Optional[list[ZonePoint]] = None  # rectangle/polygon


class UpdateZoneRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    zone_type: Optional[str] = None
    color: Optional[str] = None
    shape: Optional[str] = None
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    radius_meters: Optional[float] = None
    polygon_points: Optional[list[ZonePoint]] = None


class ZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    zone_type: Optional[str] = None
    color: Optional[str] = None
    shape: Optional[str] = "circle"
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    radius_meters: Optional[float] = None
    polygon_points: Optional[list[dict]] = None
    created_at: datetime
    updated_at: datetime


class AssignMachineRequest(BaseModel):
    machine_id: str
