from supabase import Client


def extract_domain(email: str) -> str:
    return email.split("@")[1].lower()


def get_profile(supabase: Client, user_id: str) -> dict | None:
    result = supabase.table("profiles").select("*").eq("id", user_id).execute()
    return result.data[0] if result.data else None


def create_profile(
    supabase: Client,
    *,
    user_id: str,
    email: str,
    full_name: str | None,
    avatar_url: str | None,
) -> dict:
    domain = extract_domain(email)

    # Check if email domain is in allowed_domains
    domain_result = (
        supabase.table("allowed_domains")
        .select("id")
        .eq("domain", domain)
        .eq("is_active", True)
        .execute()
    )
    status = "active" if domain_result.data else "pending"

    profile_data = {
        "id": user_id,
        "email": email,
        "full_name": full_name,
        "avatar_url": avatar_url,
        "role": "employee",
        "status": status,
        "domain": domain,
    }
    result = supabase.table("profiles").insert(profile_data).execute()
    return result.data[0]


def update_profile(supabase: Client, user_id: str, data: dict) -> dict:
    result = (
        supabase.table("profiles").update(data).eq("id", user_id).execute()
    )
    return result.data[0]


def list_profiles(
    supabase: Client,
    *,
    role: str | None = None,
    status: str | None = None,
    domain: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict], int]:
    query = supabase.table("profiles").select("*", count="exact")
    if role:
        query = query.eq("role", role)
    if status:
        query = query.eq("status", status)
    if domain:
        query = query.eq("domain", domain)

    offset = (page - 1) * per_page
    result = query.order("created_at", desc=True).range(offset, offset + per_page - 1).execute()
    return result.data, result.count or 0
