from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.crud import f2 as crud
from app.database import get_db
from app.schemas.f2 import SessionCreate, SessionResponse
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get(
    "/", response_model=PaginatedResponse[SessionResponse], summary="List sessions"
)
def list_sessions(
    round_id: int | None = Query(default=None, description="Filter by round ID"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
):
    """Retrieve sessions (qualifying, sprint, feature), optionally filtered by round."""
    items, total = crud.get_sessions(db, round_id=round_id, limit=limit, offset=offset)
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{session_id}", response_model=SessionResponse, summary="Get session")
def get_session(session_id: int, db: Session = Depends(get_db)):
    """Retrieve a single session by ID."""
    session = crud.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post(
    "/", response_model=SessionResponse, status_code=201, summary="Create session"
)
def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_api_key),
):
    """Create a new session within a round."""
    round_obj = crud.get_round(db, session_data.round_id)
    if round_obj is None:
        raise HTTPException(status_code=404, detail="Round not found")
    return crud.create_session(db, session_data)
