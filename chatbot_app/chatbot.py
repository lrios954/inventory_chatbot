import asyncio
import os
import sys
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

from chatbot_app.config import Settings
from chatbot_app.inventory_client import InventoryClient
from chatbot_app.schemas import ChatResponse


SYSTEM_INSTRUCTIONS = """
You are a helpful inventory assistant for non-technical company staff.
Answer questions about the company's car inventory using only the MCP inventory tools.
Do not invent cars, prices, VINs, statuses, locations, or availability.
You are read-only: if a user asks you to create, update, reserve, sell, or delete a car,
explain that you can help them find inventory but cannot modify it.
When showing cars, include the id, VIN, year, make, model, status, mileage, price,
and location when available. Keep answers concise and easy to scan.
If a question is ambiguous, use the broadest reasonable search and suggest useful filters.
""".strip()


class ChatbotService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.inventory = InventoryClient(
            base_url=settings.inventory_api_url,
            timeout=settings.request_timeout_seconds,
        )

    async def chat(
        self,
        message: str,
        previous_response_id: str | None = None,
    ) -> ChatResponse:
        # The Strands agent is single-turn for now. Keep this parameter accepted
        # for backwards-compatible clients while the service uses MCP tools.
        _ = previous_response_id

        try:
            answer, tool_names = await asyncio.to_thread(self._run_agent, message)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Chatbot agent failed: {exc}",
            ) from exc

        return ChatResponse(
            answer=answer,
            response_id=f"chat_{uuid4().hex}",
            mcp_tools=tool_names,
        )

    def _run_agent(self, message: str) -> tuple[str, list[str]]:
        model = BedrockModel(
            model_id=self.settings.bedrock_model_id,
            region_name=self.settings.aws_region,
            max_tokens=self.settings.max_tokens,
            temperature=self.settings.temperature,
        )

        mcp_client = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command=sys.executable,
                    args=["-m", "chatbot_app.mcp_server"],
                    env={
                        **os.environ,
                        "INVENTORY_API_URL": self.settings.inventory_api_url,
                        "REQUEST_TIMEOUT_SECONDS": str(
                            self.settings.request_timeout_seconds
                        ),
                    },
                )
            )
        )

        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(
                model=model,
                tools=tools,
                system_prompt=SYSTEM_INSTRUCTIONS,
            )
            result = agent(message)

        return _agent_result_to_text(result), [_tool_name(tool) for tool in tools]


def _agent_result_to_text(result: Any) -> str:
    message = getattr(result, "message", None)
    if isinstance(message, dict):
        return _content_to_text(message.get("content"))

    content = getattr(message, "content", None)
    if content is not None:
        return _content_to_text(content)

    text = getattr(result, "text", None)
    if isinstance(text, str) and text:
        return text

    return str(result)


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
            elif hasattr(item, "text") and isinstance(item.text, str):
                parts.append(item.text)
        if parts:
            return "\n".join(parts)

    return str(content)


def _tool_name(tool: Any) -> str:
    if isinstance(tool, dict):
        name = tool.get("name") or tool.get("tool_name")
        if isinstance(name, str):
            return name

    for attribute in ("tool_name", "name"):
        name = getattr(tool, attribute, None)
        if isinstance(name, str):
            return name

    return str(tool)
