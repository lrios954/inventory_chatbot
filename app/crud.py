from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas


def create_car(db: Session, car: schemas.CarCreate) -> models.Car:
    db_car = models.Car(**car.model_dump())
    db.add(db_car)
    db.commit()
    db.refresh(db_car)
    return db_car


def get_car(db: Session, car_id: int) -> models.Car | None:
    return db.get(models.Car, car_id)


def get_car_by_vin(db: Session, vin: str) -> models.Car | None:
    return db.scalar(select(models.Car).where(models.Car.vin == vin))


def list_cars(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
) -> list[models.Car]:
    statement = select(models.Car).order_by(models.Car.id)
    if status:
        statement = statement.where(models.Car.status == status)
    statement = statement.offset(skip).limit(limit)
    return list(db.scalars(statement))


def update_car(
    db: Session,
    db_car: models.Car,
    car_update: schemas.CarUpdate,
) -> models.Car:
    for field, value in car_update.model_dump(exclude_unset=True).items():
        setattr(db_car, field, value)
    db.add(db_car)
    db.commit()
    db.refresh(db_car)
    return db_car


def delete_car(db: Session, db_car: models.Car) -> None:
    db.delete(db_car)
    db.commit()
