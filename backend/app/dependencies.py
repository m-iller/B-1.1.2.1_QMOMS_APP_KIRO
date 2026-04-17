from collections.abc import AsyncGenerator
from typing import Any
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import AsyncSessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Any:
    from app.modules.auth.repository import get_user_by_id
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

def require_roles(roles: list[str]):
    async def _check(current_user: Any = Depends(get_current_user)) -> Any:
        if not hasattr(current_user, "role") or current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return current_user
    return _check
