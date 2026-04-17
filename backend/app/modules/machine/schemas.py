from typing import Optional
from pydantic import BaseModel, ConfigDict


class CreateMachineRequest(BaseModel):
    name: str
    type: str  # excavator|haul_truck|drill|dozer|grader
    initial_state: str = "idle"


class UpdateMachineStateRequest(BaseModel):
    state: str  # idle|operating|maintenance|breakdown


class AssignDispatcherRequest(BaseModel):
    dispatcher_id: str


class MachineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: str
    current_state: str
    conflict_active: bool
    assigned_dispatcher_id: Optional[str]
    current_zone_id: Optional[str]
    pos_x: Optional[float]
    pos_y: Optional[float]
    created_at: str


class ConflictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    machine_id: str
    dispatcher_state: str
    operator_state: str
    resolved: bool
    resolved_by_user_id: Optional[str]
    resolved_at: Optional[str]
    created_at: str
