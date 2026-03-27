from dataclasses import dataclass

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings

security = HTTPBearer()


@dataclass
class AuthUser:
    id: str
    email: str
    full_name: str = ""
    avatar_url: str | None = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthUser:
    settings = get_settings()
    try:
        payload = pyjwt.decode(
            credentials.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_metadata = payload.get("user_metadata", {})
    return AuthUser(
        id=payload["sub"],
        email=payload.get("email", ""),
        full_name=user_metadata.get("full_name", user_metadata.get("name", "")),
        avatar_url=user_metadata.get("avatar_url", user_metadata.get("picture")),
    )
