from fastapi import FastAPI

from app.database import engine, Base
from app import models  # noqa: F401 — ensures models are registered before create_all
from app.routers import seasons, rounds, sessions, drivers, teams, results

app = FastAPI(
    title="F2 API",
    description="Formula 2 standings, schedule, and results",
    version="dev",
)

# Create all tables on startup
Base.metadata.create_all(bind=engine)

# Routers
app.include_router(seasons.router)
app.include_router(rounds.router)
app.include_router(sessions.router)
app.include_router(drivers.router)
app.include_router(teams.router)
app.include_router(results.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
