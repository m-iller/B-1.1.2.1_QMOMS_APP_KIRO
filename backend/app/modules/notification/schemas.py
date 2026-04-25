from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NotificationPayload(BaseModel):
    """Structured payload for all notifications."""
    name: str
    desc: str
    bigdesc: str = ""
    date: str = ""        # human-readable date e.g. "2026-04-25"
    timestamp: str = ""   # ISO timestamp


class SendNotificationRequest(BaseModel):
    """Body for POST /notifications (manual send)."""
    user_id: str
    type: str             # alert | conflict | system
    name: str
    desc: str
    bigdesc: str = ""
    date: str = ""
    timestamp: str = ""


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    type: str
    payload: dict
    read: bool
    shift_id: Optional[str] = None
    created_at: datetime
