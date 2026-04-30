from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CreateMachineRequest(BaseModel):
    name: str
    type: str  # excavator|haul_truck|drill|dozer|grader
    description: Optional[str] = None
    initial_state: str = "idle"
    enabled_sensors: list[str] = ["engine_temp", "fuel_level", "speed", "payload_weight"]


class UpdateMachineConfigRequest(BaseModel):
    description: Optional[str] = None
    enabled_sensors: Optional[list[str]] = None


class UpdateMachineStateRequest(BaseModel):
    state: str  # idle|operating|maintenance|breakdown


class AssignDispatcherRequest(BaseModel):
    dispatcher_id: str


class ResolveConflictRequest(BaseModel):
    resolution: str  # "dispatcher" | "operator" — which state to keep


class MachineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: str
    description: Optional[str] = None
    current_state: str
    conflict_active: bool
    enabled_sensors: list[str] = []
    assigned_dispatcher_id: Optional[str] = None
    current_zone_id: Optional[str] = None
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    created_at: datetime


class ConflictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    machine_id: str
    dispatcher_state: str
    operator_state: str
    resolved: bool
    resolved_by_user_id: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
