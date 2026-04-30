from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class Waypoint(BaseModel):
    lat: float
    lng: float


class CreateRouteRequest(BaseModel):
    machine_id: str
    name: str = "Route"
    waypoints: list[Waypoint]
    color: str = "#ef4444"


class UpdateRouteRequest(BaseModel):
    name: Optional[str] = None
    waypoints: Optional[list[Waypoint]] = None
    color: Optional[str] = None


class RouteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    machine_id: str
    name: str
    waypoints: list[dict]
    color: str
    created_at: datetime
    updated_at: datetime
