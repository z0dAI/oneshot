from fastapi import FastAPI

from app.routes.admin import router as admin_router
from app.routes.me import router as me_router

app = FastAPI(title="Clay Talent Portal")

app.include_router(me_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
