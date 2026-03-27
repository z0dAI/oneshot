from supabase import create_client, Client

_client: Client | None = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        from app.config import get_settings

        settings = get_settings()
        _client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _client


def reset_client() -> None:
    """Reset the client. Used in tests."""
    global _client
    _client = None
