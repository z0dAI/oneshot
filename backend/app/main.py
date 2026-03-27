from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client

from app.config import settings
from app.routes.admin import router as admin_router
from app.routes.me import router as me_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create Supabase client (service role — full access)
    app.state.supabase = create_client(
        settings.supabase_url, settings.supabase_service_role_key
    )

    # Seed admin: promote the configured email to admin on startup
    if settings.seed_admin_email:
        result = (
            app.state.supabase.table("profiles")
            .select("id, role")
            .eq("email", settings.seed_admin_email)
            .execute()
        )
        if result.data and result.data[0]["role"] != "admin":
            app.state.supabase.table("profiles").update(
                {"role": "admin", "status": "active"}
            ).eq("id", result.data[0]["id"]).execute()

    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(me_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
