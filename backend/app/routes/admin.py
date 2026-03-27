from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import AuthUser, get_current_user
from app.models import (
    DomainCreate,
    DomainResponse,
    DomainUpdate,
    PaginatedUsers,
    ProfileResponse,
    UserUpdate,
)
from app.services.profiles import get_or_create_profile, list_profiles, update_profile
from app.services.domains import list_domains, create_domain, update_domain, delete_domain

router = APIRouter(prefix="/api/admin")


def _require_admin(user: AuthUser = Depends(get_current_user)) -> dict:
    """Dependency: user must be an active admin."""
    profile = get_or_create_profile(user.id, user.email, user.full_name, user.avatar_url)
    if profile["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {profile['status']}",
        )
    if profile["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return profile


# --- Domain endpoints ---


@router.get("/domains", response_model=list[DomainResponse])
async def get_domains(admin: dict = Depends(_require_admin)):
    return list_domains()


@router.post("/domains", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def add_domain(body: DomainCreate, admin: dict = Depends(_require_admin)):
    return create_domain(body.domain, admin["id"], body.activate_existing)


@router.patch("/domains/{domain_id}", response_model=DomainResponse)
async def patch_domain(
    domain_id: str, body: DomainUpdate, admin: dict = Depends(_require_admin)
):
    return update_domain(domain_id, body.model_dump())


@router.delete("/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_domain(domain_id: str, admin: dict = Depends(_require_admin)):
    delete_domain(domain_id)


# --- User management endpoints ---


@router.get("/users", response_model=PaginatedUsers)
async def get_users(
    page: int = 1,
    per_page: int = 20,
    role: str | None = None,
    status: str | None = None,
    domain: str | None = None,
    admin: dict = Depends(_require_admin),
):
    users, total = list_profiles(page, per_page, role, status, domain)
    return PaginatedUsers(users=users, total=total, page=page, per_page=per_page)


@router.patch("/users/{user_id}", response_model=ProfileResponse)
async def patch_user(
    user_id: str, body: UserUpdate, admin: dict = Depends(_require_admin)
):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    return update_profile(user_id, updates)
