from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.crud import f2 as crud
from app.database import get_db
from app.schemas.f2 import RoundCreate, RoundResponse
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/rounds", tags=["rounds"])


@router.get("/", response_model=PaginatedResponse[RoundResponse], summary="List rounds")
def list_rounds(
    season_id: int | None = Query(default=None, description="Filter by season ID"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
):
    """Retrieve race weekend rounds, optionally filtered by season."""
    items, total = crud.get_rounds(db, season_id=season_id, limit=limit, offset=offset)
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{round_id}", response_model=RoundResponse, summary="Get round")
def get_round(round_id: int, db: Session = Depends(get_db)):
    """Retrieve a single round by ID."""
    round_obj = crud.get_round(db, round_id)
    if round_obj is None:
        raise HTTPException(status_code=404, detail="Round not found")
    return round_obj


@router.post("/", response_model=RoundResponse, status_code=201, summary="Create round")
def create_round(
    round_data: RoundCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_api_key),
):
    """Create a new round within a season."""
    season = crud.get_season(db, round_data.season_id)
    if season is None:
        raise HTTPException(status_code=404, detail="Season not found")
    return crud.create_round(db, round_data)
