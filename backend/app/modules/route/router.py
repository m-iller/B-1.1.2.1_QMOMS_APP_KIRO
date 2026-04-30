from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_roles
from app.modules.route import repository
from app.modules.route.schemas import CreateRouteRequest, RouteResponse, UpdateRouteRequest
from app.common.exceptions import NotFoundException

router = APIRouter()


def _to_response(route) -> RouteResponse:
    return RouteResponse(
        id=str(route.id),
        machine_id=str(route.machine_id),
        name=route.name,
        waypoints=route.waypoints if route.waypoints else [],
        color=route.color,
        created_at=route.created_at,
        updated_at=route.updated_at,
    )


@router.get("", response_model=list[RouteResponse])
async def list_routes(
    db: AsyncSession = Depends(get_db),
    _actor=Depends(get_current_user),
):
    routes = await repository.get_all_routes(db)
    return [_to_response(r) for r in routes]


@router.get("/machine/{machine_id}", response_model=list[RouteResponse])
async def list_routes_for_machine(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(get_current_user),
):
    routes = await repository.get_routes_by_machine(machine_id, db)
    return [_to_response(r) for r in routes]


@router.post("", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
async def create_route(
    payload: CreateRouteRequest,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["dispatcher", "admin", "dev"])),
):
    waypoints = [w.model_dump() for w in payload.waypoints]
    route = await repository.create_route(payload.machine_id, payload.name, waypoints, payload.color, db)
    return _to_response(route)


@router.patch("/{route_id}", response_model=RouteResponse)
async def update_route(
    route_id: str,
    payload: UpdateRouteRequest,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["dispatcher", "admin", "dev"])),
):
    route = await repository.get_route_by_id(route_id, db)
    if route is None:
        raise NotFoundException(f"Route {route_id} not found")
    waypoints = [w.model_dump() for w in payload.waypoints] if payload.waypoints is not None else None
    route = await repository.update_route(route_id, payload.name, waypoints, payload.color, db)
    return _to_response(route)


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(
    route_id: str,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["dispatcher", "admin", "dev"])),
):
    route = await repository.get_route_by_id(route_id, db)
    if route is None:
        raise NotFoundException(f"Route {route_id} not found")
    await repository.delete_route(route_id, db)
