from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import AuthUser, get_current_user
from app.models import ProfileResponse, ProfileUpdate
from app.services.profiles import get_or_create_profile, update_profile

router = APIRouter(prefix="/api")


def _get_profile(user: AuthUser = Depends(get_current_user)) -> dict:
    """Look up or create profile. Used by both GET and PUT."""
    return get_or_create_profile(user.id, user.email, user.full_name, user.avatar_url)


def _require_active(profile: dict = Depends(_get_profile)) -> dict:
    if profile["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {profile['status']}",
        )
    return profile


@router.get("/me", response_model=ProfileResponse)
async def get_me(profile: dict = Depends(_get_profile)):
    return profile


@router.put("/me", response_model=ProfileResponse)
async def update_me(
    body: ProfileUpdate,
    profile: dict = Depends(_require_active),
):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        return profile
    return update_profile(profile["id"], updates)
