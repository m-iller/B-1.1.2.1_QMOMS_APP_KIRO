from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    machine_id: Optional[str] = None
    event_type: str
    payload: dict
    shift_id: Optional[str] = None
    expired: bool
    created_at: datetime


class ShiftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    active: bool


class CreateShiftRequest(BaseModel):
    name: str
    start_time: str  # ISO8601
