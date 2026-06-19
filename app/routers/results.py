from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.f2 import ResultCreate, ResultResponse, PenaltyCreate, PenaltyResponse
from app.crud import f2 as crud

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/", response_model=list[ResultResponse])
def list_results(
    session_id: int | None = Query(default=None, description="Filter by session"),
    driver_id: int | None = Query(default=None, description="Filter by driver"),
    db: Session = Depends(get_db),
):
    return crud.get_results(db, session_id=session_id, driver_id=driver_id)


@router.get("/{result_id}", response_model=ResultResponse)
def get_result(result_id: int, db: Session = Depends(get_db)):
    result = crud.get_result(db, result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@router.post("/", response_model=ResultResponse, status_code=201)
def create_result(result_data: ResultCreate, db: Session = Depends(get_db)):
    # Verify session exists
    session = crud.get_session(db, result_data.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    # Verify driver exists
    driver = crud.get_driver(db, result_data.driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    # Verify team exists
    team = crud.get_team(db, result_data.team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return crud.create_result(db, result_data)


# --- Penalties (nested under results) ---


@router.get("/{result_id}/penalties", response_model=list[PenaltyResponse])
def list_penalties(result_id: int, db: Session = Depends(get_db)):
    result = crud.get_result(db, result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return crud.get_penalties(db, result_id=result_id)


@router.post("/{result_id}/penalties", response_model=PenaltyResponse, status_code=201)
def create_penalty(
    result_id: int, penalty_data: PenaltyCreate, db: Session = Depends(get_db)
):
    result = crud.get_result(db, result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return crud.create_penalty(db, penalty_data)
