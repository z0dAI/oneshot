from fastapi import Depends, HTTPException, Request
from supabase import Client

from app.auth import get_current_user
from app.services.profiles import create_profile, get_profile


def get_supabase(request: Request) -> Client:
    return request.app.state.supabase


def get_or_create_profile(
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """Look up profile; create on first login with domain allowlist check."""
    profile = get_profile(supabase, user["id"])
    if profile:
        return profile
    return create_profile(
        supabase,
        user_id=user["id"],
        email=user["email"],
        full_name=user.get("full_name"),
        avatar_url=user.get("avatar_url"),
    )


def require_active_profile(
    profile: dict = Depends(get_or_create_profile),
) -> dict:
    """Reject pending/archived users with 403."""
    if profile["status"] != "active":
        raise HTTPException(status_code=403, detail=f"Account is {profile['status']}")
    return profile


def require_admin(
    profile: dict = Depends(require_active_profile),
) -> dict:
    """Reject non-admin users with 403."""
    if profile["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return profile
