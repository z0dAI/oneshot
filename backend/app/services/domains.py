from app.database import get_supabase


def list_domains() -> list[dict]:
    supabase = get_supabase()
    response = supabase.table("allowed_domains").select("*").execute()
    return response.data


def create_domain(domain: str, added_by: str, activate_existing: bool = False) -> dict:
    supabase = get_supabase()
    response = (
        supabase.table("allowed_domains")
        .insert({"domain": domain, "added_by": added_by})
        .execute()
    )

    if activate_existing:
        supabase.table("profiles").update({"status": "active"}).eq("domain", domain).eq(
            "status", "pending"
        ).execute()

    return response.data[0]


def update_domain(domain_id: str, updates: dict) -> dict:
    supabase = get_supabase()
    response = (
        supabase.table("allowed_domains").update(updates).eq("id", domain_id).execute()
    )
    return response.data[0]


def delete_domain(domain_id: str) -> None:
    supabase = get_supabase()
    supabase.table("allowed_domains").delete().eq("id", domain_id).execute()
