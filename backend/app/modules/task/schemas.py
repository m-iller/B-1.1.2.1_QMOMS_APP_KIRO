from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CreateTaskRequest(BaseModel):
    machine_id: str
    title: str
    description: Optional[str] = None
    priority: str  # low|medium|high|critical
    deadline: str  # ISO8601


class UpdateTaskRequest(BaseModel):
    state: Optional[str] = None  # pending|active|completed|validated


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    machine_id: str
    title: str
    description: Optional[str] = None
    priority: str
    state: str
    deadline: datetime
    pending_activation: bool
    overdue: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CreateHaulCycleRequest(BaseModel):
    machine_id: str
    origin_zone_id: str
    destination_zone_id: str
    payload_tonnes: float
    start_time: str  # ISO8601


class HaulCycleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    machine_id: str
    origin_zone_id: str
    destination_zone_id: str
    payload_tonnes: float
    status: str
    immutable: bool
    start_time: datetime
    end_time: Optional[datetime] = None
    created_at: datetime
