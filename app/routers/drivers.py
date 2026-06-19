from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.f2 import DriverCreate, DriverResponse
from app.crud import f2 as crud

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("/", response_model=list[DriverResponse])
def list_drivers(db: Session = Depends(get_db)):
    return crud.get_drivers(db)


@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    driver = crud.get_driver(db, driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.post("/", response_model=DriverResponse, status_code=201)
def create_driver(driver_data: DriverCreate, db: Session = Depends(get_db)):
    return crud.create_driver(db, driver_data)
