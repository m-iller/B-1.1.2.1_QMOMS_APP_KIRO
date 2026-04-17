from datetime import datetime
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
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AssignMachineRequest(BaseModel):
    machine_id: str
