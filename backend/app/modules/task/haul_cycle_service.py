from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.exceptions import NotFoundException, ForbiddenException
from app.modules.task import haul_cycle_repository
from app.modules.task.schemas import CreateHaulCycleRequest, HaulCycleResponse

def _to_response(hc) -> HaulCycleResponse:
    return HaulCycleResponse(
        id=str(hc.id), machine_id=str(hc.machine_id),
        origin_zone_id=str(hc.origin_zone_id), destination_zone_id=str(hc.destination_zone_id),
        payload_tonnes=hc.payload_tonnes, status=hc.status, immutable=hc.immutable,
        start_time=str(hc.start_time), end_time=str(hc.end_time) if hc.end_time else None,
        created_at=str(hc.created_at),
    )

async def find_all(db: AsyncSession) -> list[HaulCycleResponse]:
    hcs = await haul_cycle_repository.get_all_haul_cycles(db)
    return [_to_response(hc) for hc in hcs]

async def create(payload: CreateHaulCycleRequest, db: AsyncSession) -> HaulCycleResponse:
    hc = await haul_cycle_repository.create_haul_cycle(
        machine_id=payload.machine_id, origin_zone_id=payload.origin_zone_id,
        destination_zone_id=payload.destination_zone_id, payload_tonnes=payload.payload_tonnes,
        start_time=payload.start_time, db=db,
    )
    return _to_response(hc)

async def complete(haul_cycle_id: str, db: AsyncSession) -> HaulCycleResponse:
    hc = await haul_cycle_repository.get_haul_cycle_by_id(haul_cycle_id, db)
    if hc is None:
        raise NotFoundException(f"HaulCycle {haul_cycle_id} not found")
    if hc.immutable:
        raise ForbiddenException("Haul cycle is immutable after completion")
    hc = await haul_cycle_repository.complete_haul_cycle(haul_cycle_id, db)
    return _to_response(hc)
