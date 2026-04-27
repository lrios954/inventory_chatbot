from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        examples=["Show me available Toyota cars under $25,000."],
    )
    previous_response_id: str | None = Field(
        default=None,
        description="Accepted for backwards compatibility; the Strands agent is currently single-turn.",
    )


class ToolCallLog(BaseModel):
    name: str
    arguments: dict[str, Any]


class ChatResponse(BaseModel):
    answer: str
    response_id: str
    tool_calls: list[ToolCallLog] = Field(default_factory=list)
    mcp_tools: list[str] = Field(default_factory=list)
