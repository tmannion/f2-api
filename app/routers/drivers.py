from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.database import get_db
from app.schemas.f2 import DriverCreate, DriverResponse
from app.schemas.pagination import PaginatedResponse
from app.crud import f2 as crud

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("/", response_model=PaginatedResponse[DriverResponse])
def list_drivers(
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
):
    items, total = crud.get_drivers(db, limit=limit, offset=offset)
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    driver = crud.get_driver(db, driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.post("/", response_model=DriverResponse, status_code=201)
def create_driver(
    driver_data: DriverCreate,
    db: Session = Depends(get_db),
    _: str = Depends(require_api_key),
):
    return crud.create_driver(db, driver_data)
