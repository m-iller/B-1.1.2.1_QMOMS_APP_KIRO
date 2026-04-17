from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from passlib.context import CryptContext
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.modules.auth.repository import get_user_by_username
from app.modules.auth.schemas import LoginRequest, LoginResponse, UserResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def login(payload: LoginRequest, db: AsyncSession) -> LoginResponse:
    user = await get_user_by_username(payload.username, db)
    if not user or not pwd_context.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.JWT_EXPIRES_IN)
    token_data = {"sub": str(user.id), "role": user.role, "exp": expire}
    access_token = jwt.encode(token_data, settings.JWT_SECRET, algorithm="HS256")
    return LoginResponse(
        access_token=access_token,
        user=UserResponse(id=str(user.id), username=user.username, role=user.role),
    )
