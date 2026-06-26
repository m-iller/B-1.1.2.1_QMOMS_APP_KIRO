from fastapi import APIRouter, Depends
from app.dependencies import get_current_user_optional, require_roles
from app.modules.map_config.schemas import MapConfigRequest, MapConfigResponse
from app.modules.map_config.service import MapConfigService

router = APIRouter()
_service = MapConfigService()


@router.get("", response_model=MapConfigResponse)
async def get_map_config(_actor=Depends(get_current_user_optional)):  # Optional auth for simulator
    """
    Get map configuration. Authentication is optional to allow simulator to fetch map config at startup.
    """
    return _service.get()


@router.put("", response_model=MapConfigResponse)
async def put_map_config(
    body: MapConfigRequest,
    _actor=Depends(require_roles(["dispatcher", "admin"])),
):
    return _service.save(body)
