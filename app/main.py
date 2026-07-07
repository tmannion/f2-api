from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401 — ensures models are registered before create_all
from app.database import Base, engine
from app.routers import api_v1_router

app = FastAPI(
    title="F2 API",
    description="Formula 2 standings, schedule, and results",
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
