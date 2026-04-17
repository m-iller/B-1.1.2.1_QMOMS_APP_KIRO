from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notification.models import Notification


async def insert_notification(
    user_id: str,
    type_: str,
    payload: dict,
    shift_id: str | None,
    db: AsyncSession,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=type_,
        payload=payload,
        shift_id=shift_id,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def find_for_user_filtered(
    user_id: str,
    type_: str | None,
    read: bool | None,
    db: AsyncSession,
) -> list[Notification]:
    q = select(Notification).where(Notification.user_id == user_id)
    if type_ is not None:
        q = q.where(Notification.type == type_)
    if read is not None:
        q = q.where(Notification.read == read)
    result = await db.execute(q.order_by(Notification.created_at.desc()))
    return list(result.scalars().all())


async def get_by_id(notification_id: str, db: AsyncSession) -> Notification | None:
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    return result.scalar_one_or_none()


async def mark_read(notification_id: str, db: AsyncSession) -> Notification:
    notification = await get_by_id(notification_id, db)
    notification.read = True
    await db.commit()
    await db.refresh(notification)
    return notification
