from app.database import get_supabase


def get_profile(user_id: str) -> dict | None:
    supabase = get_supabase()
    response = supabase.table("profiles").select("*").eq("id", user_id).execute()
    return response.data[0] if response.data else None


def create_profile(user_id: str, email: str, full_name: str, avatar_url: str | None) -> dict:
    supabase = get_supabase()
    domain = email.split("@")[1] if "@" in email else ""

    # Check domain allowlist
    domain_response = (
        supabase.table("allowed_domains")
        .select("*")
        .eq("domain", domain)
        .eq("is_active", True)
        .execute()
    )
    status = "active" if domain_response.data else "pending"

    profile = {
        "id": user_id,
        "email": email,
        "full_name": full_name,
        "avatar_url": avatar_url,
        "role": "employee",
        "status": status,
        "domain": domain,
    }
    response = supabase.table("profiles").insert(profile).execute()
    return response.data[0]


def get_or_create_profile(
    user_id: str, email: str, full_name: str, avatar_url: str | None
) -> dict:
    profile = get_profile(user_id)
    if profile is None:
        profile = create_profile(user_id, email, full_name, avatar_url)
    return profile


def update_profile(user_id: str, updates: dict) -> dict:
    supabase = get_supabase()
    response = supabase.table("profiles").update(updates).eq("id", user_id).execute()
    return response.data[0]


def list_profiles(
    page: int = 1,
    per_page: int = 20,
    role: str | None = None,
    status: str | None = None,
    domain: str | None = None,
) -> tuple[list[dict], int]:
    supabase = get_supabase()
    query = supabase.table("profiles").select("*", count="exact")

    if role:
        query = query.eq("role", role)
    if status:
        query = query.eq("status", status)
    if domain:
        query = query.eq("domain", domain)

    offset = (page - 1) * per_page
    response = query.range(offset, offset + per_page - 1).execute()
    return response.data, response.count or 0
