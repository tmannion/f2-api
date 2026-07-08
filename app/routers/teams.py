from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.crud import f2 as crud
from app.database import get_db
from app.schemas.f2 import TeamCreate, TeamResponse
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/", response_model=PaginatedResponse[TeamResponse], summary="List teams")
def list_teams(
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
):
    """Retrieve all teams, ordered alphabetically by name."""
    items, total = crud.get_teams(db, limit=limit, offset=offset)
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{team_id}", response_model=TeamResponse, summary="Get team")
def get_team(team_id: int, db: Session = Depends(get_db)):
    """Retrieve a single team by ID."""
    team = crud.get_team(db, team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.post("/", response_model=TeamResponse, status_code=201, summary="Create team")
def create_team(
    team_data: TeamCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_api_key),
):
    """Register a new team."""
    return crud.create_team(db, team_data)
