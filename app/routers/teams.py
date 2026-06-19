from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.f2 import TeamCreate, TeamResponse
from app.crud import f2 as crud

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/", response_model=list[TeamResponse])
def list_teams(db: Session = Depends(get_db)):
    return crud.get_teams(db)


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(team_id: int, db: Session = Depends(get_db)):
    team = crud.get_team(db, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.post("/", response_model=TeamResponse, status_code=201)
def create_team(team_data: TeamCreate, db: Session = Depends(get_db)):
    return crud.create_team(db, team_data)
