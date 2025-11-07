"""GigaChat API request and response models."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class GigaChatMessage(BaseModel):
    """Message in GigaChat chat completion."""

    role: Literal["system", "user", "assistant"]
    content: str


class GigaChatUsage(BaseModel):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class GigaChatChoice(BaseModel):
    """Choice in GigaChat response."""

    message: GigaChatMessage
    index: int
    finish_reason: str


class GigaChatCompletionRequest(BaseModel):
    """Request to GigaChat chat completion API."""

    model: str = Field(default="GigaChat")
    messages: list[GigaChatMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    n: int = Field(default=1, ge=1)
    stream: bool = Field(default=False)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    repetition_penalty: float = Field(default=1.0, ge=0.0, le=2.0)
    update_interval: float = Field(default=0)


class GigaChatCompletionResponse(BaseModel):
    """Response from GigaChat chat completion API."""

    choices: list[GigaChatChoice]
    created: int
    model: str
    usage: GigaChatUsage
    object: str = "chat.completion"


class GigaChatOAuthRequest(BaseModel):
    """Request to get OAuth access token."""

    scope: str = "GIGACHAT_API_PERS"


class GigaChatOAuthResponse(BaseModel):
    """Response with OAuth access token."""

    access_token: str
    expires_at: int  # Unix timestamp


class GigaChatModel(BaseModel):
    """GigaChat model information."""

    id: str
    object: str = "model"
    owned_by: str


class GigaChatModelsResponse(BaseModel):
    """Response with list of available models."""

    data: list[GigaChatModel]
    object: str = "list"


class GigaChatError(BaseModel):
    """Error response from GigaChat API."""

    message: str
    type: str
    param: Optional[str] = None
    code: Optional[str] = None
