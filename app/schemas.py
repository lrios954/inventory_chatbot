from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


Vin = Annotated[str, Field(min_length=1, max_length=17, examples=["1HGCM82633A004352"])]
Status = Annotated[
    str,
    Field(
        min_length=1,
        max_length=30,
        examples=["available"],
        description="Examples: available, reserved, sold, maintenance",
    ),
]


class CarBase(BaseModel):
    vin: Vin
    make: str = Field(min_length=1, max_length=80, examples=["Toyota"])
    model: str = Field(min_length=1, max_length=80, examples=["Corolla"])
    year: int = Field(ge=1886, le=2100, examples=[2024])
    color: str | None = Field(default=None, max_length=50, examples=["Silver"])
    mileage: int = Field(default=0, ge=0, examples=[12500])
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2, examples=[21999.99])
    status: Status = "available"
    location: str | None = Field(default=None, max_length=120, examples=["Main lot"])


class CarCreate(CarBase):
    pass


class CarUpdate(BaseModel):
    vin: Vin | None = None
    make: str | None = Field(default=None, min_length=1, max_length=80)
    model: str | None = Field(default=None, min_length=1, max_length=80)
    year: int | None = Field(default=None, ge=1886, le=2100)
    color: str | None = Field(default=None, max_length=50)
    mileage: int | None = Field(default=None, ge=0)
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    status: Status | None = None
    location: str | None = Field(default=None, max_length=120)


class CarRead(CarBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
