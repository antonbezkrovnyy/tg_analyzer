"""Service for building prompts for GigaChat analysis."""

import json
from pathlib import Path
from typing import Literal

from src.models.message import Message, MessageDump


class PromptBuilder:
    """Builder for creating analysis prompts."""

    def __init__(
        self, template_path: Path = Path("config/prompts/analysis_prompt.txt")
    ):
        """Initialize prompt builder.

        Args:
            template_path: Path to prompt template file
        """
        self.template_path = template_path
        self.template = self._load_template()

    def _load_template(self) -> str:
        """Load prompt template from file.

        Returns:
            Template string

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")

        with open(self.template_path, encoding="utf-8") as f:
            return f.read()

    def build(
        self,
        chat_name: str,
        chat_username: str,
        date: str,
        message_dump: MessageDump,
        window_size: int = 30,
        format_style: Literal["json", "text"] = "json",
    ) -> str:
        """Build complete prompt for GigaChat.

        Args:
            chat_name: Human-readable chat name
            chat_username: Chat username for links (e.g., "ru_python")
            date: Date in YYYY-MM-DD format
            message_dump: Message dump with messages and senders
            window_size: Number of messages to include (default: 30)
            format_style: Message formatting style (default: "json")

        Returns:
            Complete prompt string ready for GigaChat
        """
        # Limit messages to window size
        messages_to_analyze = message_dump.messages[:window_size]

        # Format messages
        messages_formatted = self.format_messages(
            messages_to_analyze, message_dump.senders, style=format_style
        )

        # Fill template
        prompt = self.template.format(
            chat_name=chat_name,
            chat_username=chat_username,
            date=date,
            message_count=len(messages_to_analyze),
            messages_json=messages_formatted,
        )

        return prompt

    def format_messages(
        self,
        messages: list[Message],
        senders: dict[str, str],
        style: Literal["json", "text"] = "json",
    ) -> str:
        """Format messages for prompt.

        Args:
            messages: List of messages
            senders: Mapping of sender_id to sender name
            style: Formatting style ("json" or "text")

        Returns:
            Formatted messages string
        """
        if style == "json":
            return self._format_messages_json(messages, senders)
        else:
            return self._format_messages_text(messages, senders)

    def _format_messages_json(
        self, messages: list[Message], senders: dict[str, str]
    ) -> str:
        """Format messages as JSON array.

        Args:
            messages: List of messages
            senders: Mapping of sender_id to sender name

        Returns:
            JSON string with message metadata
        """
        formatted = []

        for msg in messages:
            sender_name = senders.get(str(msg.sender_id), "Unknown")
            formatted.append(
                {
                    "id": msg.id,
                    "timestamp": msg.date.isoformat(),
                    "sender": sender_name,
                    "text": msg.text or "",
                    "reply_to": msg.reply_to_msg_id,
                }
            )

        return json.dumps(formatted, ensure_ascii=False, indent=2)

    def _format_messages_text(
        self, messages: list[Message], senders: dict[str, str]
    ) -> str:
        """Format messages as plain text.

        Args:
            messages: List of messages
            senders: Mapping of sender_id to sender name

        Returns:
            Text-formatted messages
        """
        lines = []

        for msg in messages:
            sender_name = senders.get(str(msg.sender_id), "Unknown")
            text = msg.text or ""
            reply_marker = (
                f" (reply to {msg.reply_to_msg_id})" if msg.reply_to_msg_id else ""
            )

            lines.append(f"[{msg.id}] {sender_name}{reply_marker}: {text}")

        return "\n".join(lines)

    def reload_template(self) -> None:
        """Reload template from file.

        Useful for development when template is being edited.
        """
        self.template = self._load_template()
