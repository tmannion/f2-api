from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.f2 import SeasonCreate, SeasonResponse
from app.crud import f2 as crud

router = APIRouter(prefix="/seasons", tags=["seasons"])


@router.get("/", response_model=list[SeasonResponse])
def list_seasons(db: Session = Depends(get_db)):
    return crud.get_seasons(db)


@router.get("/{season_id}", response_model=SeasonResponse)
def get_season(season_id: int, db: Session = Depends(get_db)):
    season = crud.get_season(db, season_id)
    if season is None:
        raise HTTPException(status_code=404, detail="Season not found")
    return season


@router.post("/", response_model=SeasonResponse, status_code=201)
def create_season(season: SeasonCreate, db: Session = Depends(get_db)):
    existing = crud.get_season_by_year(db, season.year)
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Season {season.year} already exists"
        )
    return crud.create_season(db, season)
