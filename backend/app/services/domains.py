from supabase import Client


def list_domains(supabase: Client) -> list[dict]:
    result = (
        supabase.table("allowed_domains")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


def create_domain(
    supabase: Client, *, domain: str, added_by: str, activate_existing: bool = False
) -> dict:
    domain_lower = domain.lower().strip()
    result = (
        supabase.table("allowed_domains")
        .insert({"domain": domain_lower, "added_by": added_by})
        .execute()
    )

    if activate_existing:
        supabase.table("profiles").update({"status": "active"}).eq(
            "domain", domain_lower
        ).eq("status", "pending").execute()

    return result.data[0]


def update_domain(supabase: Client, domain_id: str, data: dict) -> dict:
    result = (
        supabase.table("allowed_domains")
        .update(data)
        .eq("id", domain_id)
        .execute()
    )
    return result.data[0]


def delete_domain(supabase: Client, domain_id: str) -> None:
    supabase.table("allowed_domains").delete().eq("id", domain_id).execute()
