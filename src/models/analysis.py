"""Data models for analysis results."""

from datetime import datetime

from pydantic import BaseModel, Field


class Discussion(BaseModel):
    """Single discussion topic from analysis."""

    topic: str = Field(..., description="Discussion topic name")
    keywords: list[str] = Field(
        default_factory=list, description="Keywords related to topic"
    )
    participants: list[str] = Field(
        default_factory=list, description="Active participants in discussion"
    )
    summary: str = Field(..., description="Summary of the discussion")
    expert_comment: str = Field(..., description="AI-generated expert commentary")
    message_links: list[str] = Field(
        default_factory=list, description="Links to relevant messages"
    )


class AnalysisMetadata(BaseModel):
    """Metadata about the analysis."""

    chat: str = Field(..., description="Chat name")
    chat_username: str = Field(..., description="Chat username for links")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    analyzed_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when analysis was performed",
    )
    total_messages: int = Field(..., description="Total messages in source")
    analyzed_messages: int = Field(..., description="Number of messages analyzed")
    tokens_used: int = Field(..., description="Total tokens used in API call")
    model: str = Field(..., description="GigaChat model used")
    latency_seconds: float = Field(..., description="Time taken for analysis")


class AnalysisResult(BaseModel):
    """Analysis results with discussions."""

    discussions: list[Discussion] = Field(
        default_factory=list, description="List of identified discussions"
    )
