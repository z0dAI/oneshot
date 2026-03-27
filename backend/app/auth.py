import jwt as pyjwt
from fastapi import HTTPException, Request

from app.config import settings


def get_current_user(request: Request) -> dict:
    """Validate Supabase JWT from Authorization header. Returns user info dict."""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = auth_header[7:]
    try:
        payload = pyjwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_meta = payload.get("user_metadata", {})
    return {
        "id": payload["sub"],
        "email": payload.get("email", ""),
        "full_name": user_meta.get("full_name"),
        "avatar_url": user_meta.get("avatar_url"),
    }
