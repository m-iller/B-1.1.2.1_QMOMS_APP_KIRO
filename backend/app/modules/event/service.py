from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.event import repository
from app.modules.event.schemas import EventResponse, ShiftResponse


class EventService:
    async def emit(
        self,
        machine_id: str | None,
        event_type: str,
        payload: dict,
        db: AsyncSession,
    ) -> EventResponse:
        active_shift = await repository.get_active_shift(db)
        shift_id = active_shift.id if active_shift else None
        event = await repository.insert_event(
            machine_id=machine_id,
            event_type=event_type,
            payload=payload,
            shift_id=shift_id,
            db=db,
        )
        return _to_event_response(event)

    async def find_all(
        self,
        machine_id: str | None,
        event_type: str | None,
        shift_id: str | None,
        db: AsyncSession,
    ) -> list[EventResponse]:
        events = await repository.find_all_filtered(machine_id, event_type, shift_id, db)
        return [_to_event_response(e) for e in events]

    async def expire_shift_events(self, shift_id: str, db: AsyncSession) -> None:
        await repository.expire_by_shift_id(shift_id, db)


def _to_event_response(event) -> EventResponse:
    return EventResponse(
        id=str(event.id),
        machine_id=str(event.machine_id) if event.machine_id else None,
        event_type=event.event_type,
        payload=event.payload if event.payload else {},
        shift_id=str(event.shift_id) if event.shift_id else None,
        expired=event.expired,
        created_at=event.created_at,
    )
