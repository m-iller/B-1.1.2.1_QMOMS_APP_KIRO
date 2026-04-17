from typing import Optional
from pydantic import BaseModel, ConfigDict


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    machine_id: Optional[str]
    event_type: str
    payload: dict
    shift_id: Optional[str]
    expired: bool
    created_at: str


class ShiftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    start_time: str
    end_time: Optional[str]
    active: bool


class CreateShiftRequest(BaseModel):
    name: str
    start_time: str  # ISO8601
