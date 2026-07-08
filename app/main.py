from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401 — ensures models are registered before create_all
from app.database import Base, engine
from app.routers import api_v1_router

app = FastAPI(
    title="F2 API",
    description=(
        "REST API for FIA Formula 2 Championship data including "
        "standings, race schedules, session results, and driver/team information.\n\n"
        "**Public endpoints** (GET) require no authentication.\n\n"
        "**Write endpoints** (POST) require an API key via the `X-API-Key` header."
    ),
    version="dev",
)

# CORS — allow any frontend to consume this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Create all tables on startup
Base.metadata.create_all(bind=engine)

# API v1 routes
app.include_router(api_v1_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
