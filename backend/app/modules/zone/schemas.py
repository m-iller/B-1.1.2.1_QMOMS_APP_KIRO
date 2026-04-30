from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CreateZoneRequest(BaseModel):
    name: str
    description: Optional[str] = None
    zone_type: Optional[str] = None
    color: Optional[str] = None
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    radius_meters: float = 200.0


class UpdateZoneRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    zone_type: Optional[str] = None
    color: Optional[str] = None
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    radius_meters: Optional[float] = None


class ZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    zone_type: Optional[str] = None
    color: Optional[str] = None
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    radius_meters: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class AssignMachineRequest(BaseModel):
    machine_id: str
