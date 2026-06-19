from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.standings import StandingsResponse
from app.crud import f2 as crud

router = APIRouter(prefix="/standings", tags=["standings"])


@router.get("/", response_model=StandingsResponse)
def get_standings(
    season_id: int = Query(description="Season ID to calculate standings for"),
    db: Session = Depends(get_db),
):
    season = crud.get_season(db, season_id)
    if season is None:
        raise HTTPException(status_code=404, detail="Season not found")

    standings = crud.get_standings(db, season_id)
    return StandingsResponse(
        season_id=season.id,
        season_year=season.year,
        standings=standings,
    )
