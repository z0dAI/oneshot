from fastapi import APIRouter, Depends
from supabase import Client

from app.dependencies import get_or_create_profile, get_supabase, require_active_profile
from app.models import ProfileResponse, ProfileUpdate
from app.services.profiles import update_profile

router = APIRouter()


@router.get("/me", response_model=ProfileResponse)
def get_me(profile: dict = Depends(get_or_create_profile)):
    """Return current user's profile. Accessible even for pending/archived users."""
    return profile


@router.put("/me", response_model=ProfileResponse)
def update_me(
    body: ProfileUpdate,
    profile: dict = Depends(require_active_profile),
    supabase: Client = Depends(get_supabase),
):
    """Update own profile (name/avatar only). Requires active status."""
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        return profile
    return update_profile(supabase, profile["id"], update_data)
