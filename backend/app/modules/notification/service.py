from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ForbiddenException, NotFoundException
from app.modules.event.repository import get_active_shift
from app.modules.notification import repository
from app.modules.notification.schemas import NotificationResponse


class NotificationService:
    async def create(
        self,
        user_id: str,
        type_: str,
        payload: dict,
        db: AsyncSession,
        shift_id: str | None = None,
    ) -> NotificationResponse:
        if shift_id is None:
            active_shift = await get_active_shift(db)
            shift_id = active_shift.id if active_shift else None
        notification = await repository.insert_notification(user_id, type_, payload, shift_id, db)
        return _to_response(notification)

    async def find_for_user(
        self,
        user_id: str,
        type_: str | None,
        read: bool | None,
        db: AsyncSession,
    ) -> list[NotificationResponse]:
        notifications = await repository.find_for_user_filtered(user_id, type_, read, db)
        return [_to_response(n) for n in notifications]

    async def mark_read(
        self,
        notification_id: str,
        requesting_user,
        db: AsyncSession,
    ) -> NotificationResponse:
        notification = await repository.get_by_id(notification_id, db)
        if notification is None:
            raise NotFoundException("Notification not found")
        if str(notification.user_id) != str(requesting_user.id):
            raise ForbiddenException()
        updated = await repository.mark_read(notification_id, db)
        return _to_response(updated)


def _to_response(notification) -> NotificationResponse:
    return NotificationResponse(
        id=str(notification.id),
        user_id=str(notification.user_id),
        type=notification.type,
        payload=notification.payload if notification.payload else {},
        read=notification.read,
        shift_id=str(notification.shift_id) if notification.shift_id else None,
        created_at=notification.created_at,
    )
