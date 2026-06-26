from typing import Any
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import AsyncSessionLocal

# Use HTTPBearer instead of OAuth2PasswordBearer for more flexibility
bearer_scheme = HTTPBearer(auto_error=False)  # auto_error=False allows optional auth

from collections.abc import AsyncGenerator

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Any:
    from app.modules.auth.repository import get_user_by_id
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await get_user_by_id(user_id, db)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Any | None:
    """
    Optional authentication for simulator endpoints.
    Returns None if no credentials provided, otherwise validates and returns user.
    """
    if not credentials:
        return None
    token = credentials.credentials
    try:
        from app.modules.auth.repository import get_user_by_id
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        user = await get_user_by_id(user_id, db)
        return user
    except (ExpiredSignatureError, JWTError):
        return None

def require_roles(roles: list[str]):
    async def _check(current_user: Any = Depends(get_current_user)) -> Any:
        # 'dev' role has all permissions — bypasses every role check
        if not hasattr(current_user, "role"):
            raise HTTPException(status_code=403, detail="Insufficient role")
        if current_user.role == "dev" or current_user.role in roles:
            return current_user
        raise HTTPException(status_code=403, detail="Insufficient role")
    return _check
