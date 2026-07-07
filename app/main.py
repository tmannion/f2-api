from fastapi import FastAPI

from app import models  # noqa: F401 — ensures models are registered before create_all
from app.database import Base, engine
from app.routers import api_v1_router

app = FastAPI(
    title="F2 API",
    description="Formula 2 standings, schedule, and results",
    version="dev",
)

# Create all tables on startup
Base.metadata.create_all(bind=engine)

# API v1 routes
app.include_router(api_v1_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
