"""Data models for analysis results."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ExpertComment(BaseModel):
    """Structured expert commentary for discussion."""

    problem_analysis: str = Field(..., description="Brief analysis of the problem")
    common_mistakes: list[str] = Field(
        default_factory=list, description="Common mistakes related to topic"
    )
    best_practices: list[str] = Field(
        default_factory=list, description="Recommended approaches/patterns"
    )
    actionable_insights: list[str] = Field(
        default_factory=list,
        description="Concrete actions to solve the problem",
    )
    learning_resources: list[str] = Field(
        default_factory=list, description="Links to documentation/articles"
    )


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
    expert_comment: ExpertComment | str = Field(
        ..., description="Structured expert commentary or legacy string"
    )
    message_links: list[str] = Field(
        default_factory=list, description="Links to relevant messages"
    )

    # New quality metrics fields
    priority: Literal["high", "medium", "low"] = Field(
        default="medium", description="Discussion priority level"
    )
    participant_count: int = Field(
        default=0, description="Number of unique participants"
    )
    message_count: int = Field(
        default=0, description="Number of messages in discussion"
    )
    complexity: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Topic complexity (1=basic, 5=advanced)",
    )
    sentiment: Literal["positive", "negative", "neutral", "mixed"] = Field(
        default="neutral", description="Overall sentiment of discussion"
    )
    practical_value: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Practical value for developers (1=low, 10=high)",
    )

    @field_validator("participants")
    @classmethod
    def validate_participants(cls, v: list[str]) -> list[str]:
        """Ensure participants is array of strings, not comma-separated."""
        if len(v) == 1 and "," in v[0]:
            # Split if it's a comma-separated string
            return [p.strip() for p in v[0].split(",")]
        return v


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

    # New analytics field
    discussion_stats: dict[str, Any] = Field(
        default_factory=dict, description="Statistics about discussions"
    )


class AnalysisResult(BaseModel):
    """Analysis results with discussions."""

    discussions: list[Discussion] = Field(
        default_factory=list, description="List of identified discussions"
    )
