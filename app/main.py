from fastapi import FastAPI
from app.database import engine, Base
from app import models  # noqa: F401 — ensures models are registered before create_all

app = FastAPI(
    title="F2 API",
    description="Formula 2 standings, schedule, and results",
    version="0.1.0",
)

# Create all tables on startup
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}
