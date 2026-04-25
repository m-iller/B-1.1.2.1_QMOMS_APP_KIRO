import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ForbiddenException, NotFoundException
from app.common.roles import OPERATIONAL_NOTIFY_ROLES
from app.modules.event.repository import get_active_shift
from app.modules.notification import repository
from app.modules.notification.schemas import NotificationResponse

logger = logging.getLogger(__name__)


def _build_payload(
    name: str,
    desc: str,
    bigdesc: str = "",
    date: str = "",
    timestamp: str = "",
) -> dict:
    if not timestamp:
        timestamp = datetime.now(timezone.utc).isoformat()
    if not date:
        # Extract date portion from ISO timestamp reliably
        date = datetime.fromisoformat(timestamp).date().isoformat()
    return {"name": name, "desc": desc, "bigdesc": bigdesc, "date": date, "timestamp": timestamp}


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

    async def send(
        self,
        user_id: str,
        type_: str,
        name: str,
        desc: str,
        bigdesc: str,
        date: str,
        timestamp: str,
        db: AsyncSession,
    ) -> NotificationResponse:
        payload = _build_payload(name, desc, bigdesc, date, timestamp)
        return await self.create(user_id, type_, payload, db)

    async def broadcast_to_roles(
        self,
        roles: list[str],
        type_: str,
        name: str,
        desc: str,
        bigdesc: str,
        db: AsyncSession,
    ) -> None:
        """Send notification to all users with the given roles."""
        from app.modules.auth.repository import get_users_by_roles
        users = await get_users_by_roles(roles, db)
        payload = _build_payload(name, desc, bigdesc)
        active_shift = await get_active_shift(db)
        shift_id = active_shift.id if active_shift else None
        for user in users:
            await repository.insert_notification(str(user.id), type_, payload, shift_id, db)

    async def notify_task_created(self, task, db: AsyncSession) -> None:
        await self.broadcast_to_roles(
            roles=list(OPERATIONAL_NOTIFY_ROLES),
            type_="system",
            name=f"Task Created: {task.title}",
            desc=f"Priority: {task.priority} | Machine: {task.machine_id}",
            bigdesc=task.description or "",
            db=db,
        )

    async def notify_task_state_changed(self, task, previous_state: str, db: AsyncSession) -> None:
        await self.broadcast_to_roles(
            roles=list(OPERATIONAL_NOTIFY_ROLES),
            type_="system",
            name=f"Task Updated: {task.title}",
            desc=f"State: {previous_state} → {task.state} | Priority: {task.priority}",
            bigdesc=task.description or "",
            db=db,
        )

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
