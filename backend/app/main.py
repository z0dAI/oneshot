from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import get_supabase
from app.routes.me import router as me_router
from app.routes.admin import router as admin_router


def _seed_admin() -> None:
    """Promote the seed admin email to admin role on startup."""
    settings = get_settings()
    if not settings.seed_admin_email:
        return

    supabase = get_supabase()
    response = (
        supabase.table("profiles")
        .select("id, role")
        .eq("email", settings.seed_admin_email)
        .execute()
    )
    if not response.data:
        return

    profile = response.data[0]
    if profile["role"] != "admin":
        supabase.table("profiles").update({"role": "admin", "status": "active"}).eq(
            "id", profile["id"]
        ).execute()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _seed_admin()
    yield


app = FastAPI(title="Clay Talent Portal API", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(me_router)
app.include_router(admin_router)
