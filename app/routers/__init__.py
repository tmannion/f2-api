from fastapi import APIRouter

from app.routers import drivers, results, rounds, seasons, sessions, standings, teams

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(seasons.router)
api_v1_router.include_router(rounds.router)
api_v1_router.include_router(sessions.router)
api_v1_router.include_router(drivers.router)
api_v1_router.include_router(teams.router)
api_v1_router.include_router(results.router)
api_v1_router.include_router(standings.router)
