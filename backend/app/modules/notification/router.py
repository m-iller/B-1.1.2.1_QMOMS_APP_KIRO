from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_roles
from app.modules.notification.schemas import NotificationResponse, SendNotificationRequest
from app.modules.notification.service import NotificationService

router = APIRouter()
_service = NotificationService()


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    type: Optional[str] = Query(None),
    read: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await _service.find_for_user(str(current_user.id), type, read, db)


@router.post("", response_model=NotificationResponse, status_code=201)
async def send_notification(
    payload: SendNotificationRequest,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["dispatcher", "admin", "dev"])),
):
    return await _service.send(
        user_id=payload.user_id,
        type_=payload.type,
        name=payload.name,
        desc=payload.desc,
        bigdesc=payload.bigdesc,
        date=payload.date,
        timestamp=payload.timestamp,
        db=db,
    )


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await _service.mark_read(notification_id, current_user, db)
