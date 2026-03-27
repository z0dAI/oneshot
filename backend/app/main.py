from fastapi import FastAPI

app = FastAPI(title="Clay Talent Portal")


@app.get("/api/health")
def health():
    return {"status": "ok"}
