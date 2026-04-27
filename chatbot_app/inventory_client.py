from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import quote

import httpx


class InventoryClient:
    def __init__(self, base_url: str, timeout: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        ) as client:
            response = await client.get("/health")
            response.raise_for_status()
            return response.json()

    async def list_cars(
        self,
        status: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status

        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        ) as client:
            response = await client.get("/cars", params=params)
            response.raise_for_status()
            return response.json()

    async def get_car_by_id(self, car_id: int) -> dict[str, Any] | None:
        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        ) as client:
            response = await client.get(f"/cars/{car_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def get_car_by_vin(self, vin: str) -> dict[str, Any] | None:
        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        ) as client:
            response = await client.get(f"/cars/vin/{quote(vin)}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def search_cars(
        self,
        make: str | None = None,
        model: str | None = None,
        year: int | None = None,
        min_year: int | None = None,
        max_year: int | None = None,
        color: str | None = None,
        status: str | None = None,
        max_mileage: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        location: str | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        cars = await self.list_cars(status=status, limit=500)
        filtered = [
            car
            for car in cars
            if _matches_text(car, "make", make)
            and _matches_text(car, "model", model)
            and _matches_text(car, "color", color)
            and _matches_text(car, "location", location)
            and _matches_number(
                car,
                "year",
                exact=year,
                minimum=min_year,
                maximum=max_year,
            )
            and _matches_number(car, "mileage", maximum=max_mileage)
            and _matches_money(car, "price", minimum=min_price, maximum=max_price)
        ]

        safe_limit = max(1, min(limit, 50))
        return {
            "count": len(filtered),
            "cars": filtered[:safe_limit],
            "truncated": len(filtered) > safe_limit,
        }

    async def inventory_summary(self) -> dict[str, Any]:
        cars = await self.list_cars(limit=500)
        status_counts: dict[str, int] = {}
        make_counts: dict[str, int] = {}

        for car in cars:
            status = str(car.get("status") or "unknown")
            make = str(car.get("make") or "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            make_counts[make] = make_counts.get(make, 0) + 1

        return {
            "total_cars": len(cars),
            "status_counts": status_counts,
            "make_counts": make_counts,
        }


def _matches_text(car: dict[str, Any], field: str, expected: str | None) -> bool:
    if not expected:
        return True
    value = car.get(field)
    return value is not None and expected.lower() in str(value).lower()


def _matches_number(
    car: dict[str, Any],
    field: str,
    exact: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
) -> bool:
    value = car.get(field)
    if value is None:
        return False

    try:
        number = int(value)
    except (TypeError, ValueError):
        return False
    if exact is not None and number != exact:
        return False
    if minimum is not None and number < minimum:
        return False
    if maximum is not None and number > maximum:
        return False
    return True


def _matches_money(
    car: dict[str, Any],
    field: str,
    minimum: float | None = None,
    maximum: float | None = None,
) -> bool:
    if minimum is None and maximum is None:
        return True

    value = car.get(field)
    if value is None:
        return False

    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return False

    if minimum is not None and amount < Decimal(str(minimum)):
        return False
    if maximum is not None and amount > Decimal(str(maximum)):
        return False
    return True
