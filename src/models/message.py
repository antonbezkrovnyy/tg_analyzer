"""Data models for Telegram messages (from tg_fetcher)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Reaction(BaseModel):
    """Reaction to a message."""

    emoji: str
    count: int
    users: Optional[list[int]] = None


class MessageComment(BaseModel):
    """Comment in Telegram channel post (only for channels)."""

    id: int
    date: datetime
    text: Optional[str] = None
    sender_id: int
    reply_to_msg_id: Optional[int] = None
    forward_from: Optional[str] = None
    reactions: list[Reaction] = Field(default_factory=list)
    # Comments can't have nested comments
    comments: list = Field(default_factory=list)


class Message(BaseModel):
    """Telegram message from tg_fetcher dump."""

    id: int
    date: datetime
    text: Optional[str] = None
    sender_id: int
    reply_to_msg_id: Optional[int] = None
    forward_from: Optional[str] = None
    reactions: list[Reaction] = Field(default_factory=list)
    # Comments only for channels, empty list for chats
    comments: list[MessageComment] = Field(default_factory=list)

    def is_reply(self) -> bool:
        """Check if message is a reply to another message.

        Returns:
            True if message is a reply
        """
        return self.reply_to_msg_id is not None

    def has_comments(self) -> bool:
        """Check if message has comments (channel feature).

        Returns:
            True if message has comments
        """
        return len(self.comments) > 0


class SourceInfo(BaseModel):
    """Information about message source (chat/channel)."""

    id: str
    title: str
    url: str
    type: str  # "channel", "chat", "supergroup"

    def is_channel(self) -> bool:
        """Check if source is a channel (has comments feature).

        Returns:
            True if source is a channel
        """
        return self.type == "channel"

    def is_chat(self) -> bool:
        """Check if source is a chat/supergroup (no comments).

        Returns:
            True if source is a chat or supergroup
        """
        return self.type in ("chat", "supergroup")


class MessageDump(BaseModel):
    """Complete message dump from tg_fetcher."""

    version: str
    source_info: SourceInfo
    senders: dict[str, str]  # sender_id -> sender_name
    messages: list[Message]

    def get_sender_name(self, sender_id: int) -> str:
        """Get sender name by ID.

        Args:
            sender_id: Sender ID

        Returns:
            Sender name or "Unknown" if not found
        """
        return self.senders.get(str(sender_id), "Unknown")

    def get_message_url(self, message_id: int) -> str:
        """Get Telegram message URL.

        Args:
            message_id: Message ID

        Returns:
            Direct link to message
        """
        return f"{self.source_info.url}/{message_id}"
