from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.f2 import SessionCreate, SessionResponse
from app.crud import f2 as crud

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/", response_model=list[SessionResponse])
def list_sessions(
    round_id: int | None = Query(default=None, description="Filter by round"),
    db: Session = Depends(get_db),
):
    return crud.get_sessions(db, round_id=round_id)


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = crud.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/", response_model=SessionResponse, status_code=201)
def create_session(session_data: SessionCreate, db: Session = Depends(get_db)):
    round_obj = crud.get_round(db, session_data.round_id)
    if round_obj is None:
        raise HTTPException(status_code=404, detail="Round not found")
    return crud.create_session(db, session_data)
