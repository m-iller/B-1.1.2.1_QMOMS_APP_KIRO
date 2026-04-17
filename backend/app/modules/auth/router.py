from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.modules.auth.schemas import LoginRequest, LoginResponse, UserResponse
from app.modules.auth.service import login

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login_endpoint(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with JSON body — used by the frontend."""
    return await login(payload, db)


@router.post("/token", response_model=LoginResponse)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Login with form data — used by Swagger UI Authorize button."""
    payload = LoginRequest(username=form_data.username, password=form_data.password)
    return await login(payload, db)


@router.get("/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user)):
    return UserResponse(id=str(current_user.id), username=current_user.username, role=current_user.role)
