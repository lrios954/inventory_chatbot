from functools import lru_cache
from typing import Any

import httpx
from fastapi import Depends, FastAPI

from chatbot_app.chatbot import ChatbotService
from chatbot_app.config import Settings, get_settings
from chatbot_app.schemas import ChatRequest, ChatResponse


app = FastAPI(
    title="Cars Inventory Chatbot API",
    description="Chatbot service for asking natural-language questions about car inventory.",
    version="0.1.0",
)


@lru_cache
def get_chatbot_service() -> ChatbotService:
    return ChatbotService(get_settings())


@app.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    service = get_chatbot_service()
    inventory_status: dict[str, Any]

    try:
        inventory_status = await service.inventory.health()
    except httpx.HTTPError as exc:
        inventory_status = {"status": "unavailable", "detail": str(exc)}

    return {
        "status": "ok",
        "inventory_api_url": settings.inventory_api_url,
        "inventory": inventory_status,
        "model_provider": "amazon-bedrock",
        "aws_region": settings.aws_region,
        "bedrock_model_id": settings.bedrock_model_id,
        "agent_framework": "strands",
        "mcp_server": "chatbot_app.mcp_server",
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: ChatbotService = Depends(get_chatbot_service),
) -> ChatResponse:
    return await service.chat(
        message=request.message,
        previous_response_id=request.previous_response_id,
    )
