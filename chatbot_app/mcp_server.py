import json
from typing import Any

import httpx
from mcp.server import FastMCP

from chatbot_app.config import get_settings
from chatbot_app.inventory_client import InventoryClient


mcp = FastMCP("Cars Inventory MCP Server")


def _inventory_client() -> InventoryClient:
    settings = get_settings()
    return InventoryClient(
        base_url=settings.inventory_api_url,
        timeout=settings.request_timeout_seconds,
    )


def _json_result(payload: Any) -> str:
    return json.dumps(payload, default=str)


@mcp.tool(description="Check whether the cars inventory API is reachable.")
async def inventory_health() -> str:
    try:
        result = await _inventory_client().health()
    except httpx.HTTPError as exc:
        result = {"status": "unavailable", "detail": str(exc)}
    return _json_result(result)


@mcp.tool(description="List cars from the inventory API, optionally filtered by status.")
async def list_cars(status: str | None = None, limit: int = 100) -> str:
    try:
        safe_limit = max(1, min(limit, 500))
        result = await _inventory_client().list_cars(status=status, limit=safe_limit)
    except httpx.HTTPError as exc:
        result = {"error": f"Inventory API request failed: {exc}"}
    return _json_result(result)


@mcp.tool(description="Get one car from inventory by numeric car id.")
async def get_car_by_id(car_id: int) -> str:
    try:
        result = await _inventory_client().get_car_by_id(car_id=car_id)
    except httpx.HTTPError as exc:
        result = {"error": f"Inventory API request failed: {exc}"}
    return _json_result(result or {"error": "Car not found."})


@mcp.tool(description="Get one car from inventory by VIN.")
async def get_car_by_vin(vin: str) -> str:
    try:
        result = await _inventory_client().get_car_by_vin(vin=vin)
    except httpx.HTTPError as exc:
        result = {"error": f"Inventory API request failed: {exc}"}
    return _json_result(result or {"error": "Car not found."})


@mcp.tool(
    description=(
        "Search cars using make, model, year, price, mileage, status, color, "
        "and location filters."
    )
)
async def search_cars(
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
) -> str:
    try:
        result = await _inventory_client().search_cars(
            make=make,
            model=model,
            year=year,
            min_year=min_year,
            max_year=max_year,
            color=color,
            status=status,
            max_mileage=max_mileage,
            min_price=min_price,
            max_price=max_price,
            location=location,
            limit=limit,
        )
    except httpx.HTTPError as exc:
        result = {"error": f"Inventory API request failed: {exc}"}
    return _json_result(result)


@mcp.tool(description="Summarize inventory totals grouped by status and make.")
async def get_inventory_summary() -> str:
    try:
        result = await _inventory_client().inventory_summary()
    except httpx.HTTPError as exc:
        result = {"error": f"Inventory API request failed: {exc}"}
    return _json_result(result)


if __name__ == "__main__":
    mcp.run()
