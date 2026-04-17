from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_roles
from app.modules.event import repository
from app.modules.event.schemas import CreateShiftRequest, EventResponse, ShiftResponse
from app.modules.event.service import EventService

router = APIRouter()
_event_service = EventService()


@router.get("/events", response_model=list[EventResponse])
async def list_events(
    machine_id: str | None = Query(None),
    event_type: str | None = Query(None),
    shift_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["manager", "dispatcher", "admin", "owner"])),
):
    return await _event_service.find_all(machine_id, event_type, shift_id, db)


@router.get("/shifts", response_model=list[ShiftResponse])
async def list_shifts(
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["admin", "manager"])),
):
    shifts = await repository.get_all_shifts(db)
    return [ShiftResponse.model_validate(s) for s in shifts]


@router.post("/shifts", response_model=ShiftResponse, status_code=201)
async def create_shift(
    payload: CreateShiftRequest,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["admin"])),
):
    shift = await repository.create_shift(payload.name, payload.start_time, db)
    return ShiftResponse.model_validate(shift)


@router.patch("/shifts/{shift_id}/end", response_model=ShiftResponse)
async def end_shift(
    shift_id: str,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["admin"])),
):
    shift = await repository.end_shift(shift_id, db)
    await _event_service.expire_shift_events(shift_id, db)
    return ShiftResponse.model_validate(shift)
