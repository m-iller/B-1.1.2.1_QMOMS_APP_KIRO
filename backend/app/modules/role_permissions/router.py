from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_roles
from app.modules.role_permissions.models import RolePermission
from app.modules.role_permissions.schemas import (
    CreateRolePermissionRequest,
    RolePermissionResponse,
    UpdateRolePermissionRequest,
)

router = APIRouter()

MANAGE_ROLES = ["dev", "manager"]


def _to_response(rp: RolePermission) -> RolePermissionResponse:
    return RolePermissionResponse(
        id=str(rp.id),
        role=rp.role,
        pages=rp.pages if rp.pages else [],
        created_at=rp.created_at,
        updated_at=rp.updated_at,
    )


@router.get("", response_model=list[RolePermissionResponse])
async def list_role_permissions(
    db: AsyncSession = Depends(get_db),
    _actor=Depends(get_current_user),
):
    """All authenticated users can read permissions (needed for nav visibility)."""
    result = await db.execute(select(RolePermission).order_by(RolePermission.role))
    return [_to_response(rp) for rp in result.scalars().all()]


@router.post("", response_model=RolePermissionResponse, status_code=201)
async def create_role_permission(
    payload: CreateRolePermissionRequest,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(MANAGE_ROLES)),
):
    existing = await db.execute(select(RolePermission).where(RolePermission.role == payload.role))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Role '{payload.role}' already exists")
    rp = RolePermission(role=payload.role, pages=payload.pages)
    db.add(rp)
    await db.commit()
    await db.refresh(rp)
    return _to_response(rp)


@router.patch("/{role}", response_model=RolePermissionResponse)
async def update_role_permission(
    role: str,
    payload: UpdateRolePermissionRequest,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(MANAGE_ROLES)),
):
    result = await db.execute(select(RolePermission).where(RolePermission.role == role))
    rp = result.scalar_one_or_none()
    if rp is None:
        raise HTTPException(status_code=404, detail=f"Role '{role}' not found")
    rp.pages = payload.pages
    rp.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(rp)
    return _to_response(rp)


@router.delete("/{role}", status_code=204)
async def delete_role_permission(
    role: str,
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(MANAGE_ROLES)),
):
    # Protect built-in roles from deletion
    protected = {"dev", "admin", "dispatcher", "operator"}
    if role in protected:
        raise HTTPException(status_code=400, detail=f"Cannot delete built-in role '{role}'")
    result = await db.execute(select(RolePermission).where(RolePermission.role == role))
    rp = result.scalar_one_or_none()
    if rp is None:
        raise HTTPException(status_code=404, detail=f"Role '{role}' not found")
    await db.delete(rp)
    await db.commit()
