from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.crud import f2 as crud
from app.database import get_db
from app.schemas.f2 import PenaltyCreate, PenaltyResponse, ResultCreate, ResultResponse
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/results", tags=["results"])


@router.get(
    "/", response_model=PaginatedResponse[ResultResponse], summary="List results"
)
def list_results(
    session_id: int | None = Query(default=None, description="Filter by session ID"),
    driver_id: int | None = Query(default=None, description="Filter by driver ID"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
):
    """Retrieve race results, optionally filtered by session and/or driver."""
    items, total = crud.get_results(
        db, session_id=session_id, driver_id=driver_id, limit=limit, offset=offset
    )
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{result_id}", response_model=ResultResponse, summary="Get result")
def get_result(result_id: int, db: Session = Depends(get_db)):
    """Retrieve a single result by ID."""
    result = crud.get_result(db, result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@router.post(
    "/", response_model=ResultResponse, status_code=201, summary="Create result"
)
def create_result(
    result_data: ResultCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_api_key),
):
    """Record a driver's result for a session. Validates that the session, driver, and team exist."""
    session = crud.get_session(db, result_data.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    driver = crud.get_driver(db, result_data.driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    team = crud.get_team(db, result_data.team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return crud.create_result(db, result_data)


# --- Penalties ---


@router.get(
    "/{result_id}/penalties",
    response_model=PaginatedResponse[PenaltyResponse],
    summary="List penalties for a result",
)
def list_penalties(
    result_id: int,
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
):
    """Retrieve all penalties issued against a specific result."""
    result = crud.get_result(db, result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    items, total = crud.get_penalties(
        db, result_id=result_id, limit=limit, offset=offset
    )
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/{result_id}/penalties",
    response_model=PenaltyResponse,
    status_code=201,
    summary="Create penalty",
)
def create_penalty(
    result_id: int,
    penalty_data: PenaltyCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_api_key),
):
    """Record a penalty against a race result."""
    result = crud.get_result(db, result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return crud.create_penalty(db, penalty_data)
