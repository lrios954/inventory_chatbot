from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import Base, engine, get_db


app = FastAPI(
    title="Cars Inventory API",
    description="Basic CRUD API for managing company car inventory.",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/cars",
    response_model=schemas.CarRead,
    status_code=status.HTTP_201_CREATED,
)
def create_car(
    car: schemas.CarCreate,
    db: Session = Depends(get_db),
) -> models.Car:
    try:
        return crud.create_car(db, car)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A car with this VIN already exists.",
        ) from exc


@app.get("/cars", response_model=list[schemas.CarRead])
def list_cars(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[models.Car]:
    return crud.list_cars(db, skip=skip, limit=limit, status=status_filter)


@app.get("/cars/vin/{vin}", response_model=schemas.CarRead)
def read_car_by_vin(vin: str, db: Session = Depends(get_db)) -> models.Car:
    db_car = crud.get_car_by_vin(db, vin)
    if db_car is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Car not found.",
        )
    return db_car


@app.get("/cars/{car_id}", response_model=schemas.CarRead)
def read_car(car_id: int, db: Session = Depends(get_db)) -> models.Car:
    db_car = crud.get_car(db, car_id)
    if db_car is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Car not found.",
        )
    return db_car


@app.patch("/cars/{car_id}", response_model=schemas.CarRead)
def update_car(
    car_id: int,
    car_update: schemas.CarUpdate,
    db: Session = Depends(get_db),
) -> models.Car:
    db_car = crud.get_car(db, car_id)
    if db_car is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Car not found.",
        )

    try:
        return crud.update_car(db, db_car, car_update)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A car with this VIN already exists.",
        ) from exc


@app.delete("/cars/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_car(car_id: int, db: Session = Depends(get_db)) -> Response:
    db_car = crud.get_car(db, car_id)
    if db_car is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Car not found.",
        )

    crud.delete_car(db, db_car)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
