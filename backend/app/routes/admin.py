from fastapi import APIRouter, Depends
from supabase import Client

from app.dependencies import get_supabase, require_admin
from app.models import (
    AdminUserUpdate,
    DomainCreate,
    DomainResponse,
    DomainUpdate,
    PaginatedUsers,
    ProfileResponse,
    Role,
    Status,
)
from app.services.domains import create_domain, delete_domain, list_domains, update_domain
from app.services.profiles import list_profiles, update_profile

router = APIRouter()


# --- User Management ---


@router.get("/admin/users", response_model=PaginatedUsers)
def get_users(
    role: Role | None = None,
    status: Status | None = None,
    domain: str | None = None,
    page: int = 1,
    per_page: int = 20,
    profile: dict = Depends(require_admin),
    supabase: Client = Depends(get_supabase),
):
    users, total = list_profiles(
        supabase,
        role=role.value if role else None,
        status=status.value if status else None,
        domain=domain,
        page=page,
        per_page=per_page,
    )
    return {"users": users, "total": total, "page": page, "per_page": per_page}


@router.patch("/admin/users/{user_id}", response_model=ProfileResponse)
def patch_user(
    user_id: str,
    body: AdminUserUpdate,
    profile: dict = Depends(require_admin),
    supabase: Client = Depends(get_supabase),
):
    update_data = body.model_dump(exclude_unset=True)
    # Convert enums to their string values for Supabase
    for key, val in update_data.items():
        if hasattr(val, "value"):
            update_data[key] = val.value
    return update_profile(supabase, user_id, update_data)


# --- Domain Management ---


@router.get("/admin/domains", response_model=list[DomainResponse])
def get_domains(
    profile: dict = Depends(require_admin),
    supabase: Client = Depends(get_supabase),
):
    return list_domains(supabase)


@router.post("/admin/domains", response_model=DomainResponse, status_code=201)
def add_domain(
    body: DomainCreate,
    profile: dict = Depends(require_admin),
    supabase: Client = Depends(get_supabase),
):
    return create_domain(
        supabase,
        domain=body.domain,
        added_by=profile["id"],
        activate_existing=body.activate_existing,
    )


@router.patch("/admin/domains/{domain_id}", response_model=DomainResponse)
def patch_domain(
    domain_id: str,
    body: DomainUpdate,
    profile: dict = Depends(require_admin),
    supabase: Client = Depends(get_supabase),
):
    return update_domain(supabase, domain_id, body.model_dump())


@router.delete("/admin/domains/{domain_id}", status_code=204)
def remove_domain(
    domain_id: str,
    profile: dict = Depends(require_admin),
    supabase: Client = Depends(get_supabase),
):
    delete_domain(supabase, domain_id)
