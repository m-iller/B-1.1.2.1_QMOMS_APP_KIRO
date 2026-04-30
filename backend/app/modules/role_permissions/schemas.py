from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CreateRolePermissionRequest(BaseModel):
    role: str
    pages: list[str] = []


class UpdateRolePermissionRequest(BaseModel):
    pages: list[str]


class RolePermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    pages: list[str]
    created_at: datetime
    updated_at: datetime
