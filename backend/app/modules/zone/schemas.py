from typing import Optional
from pydantic import BaseModel, ConfigDict


class CreateZoneRequest(BaseModel):
    name: str
    description: Optional[str] = None


class UpdateZoneRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: Optional[str]
    created_at: str
    updated_at: str


class AssignMachineRequest(BaseModel):
    machine_id: str
