"""Repository for reading message dumps from tg_fetcher."""

import json
import logging
from pathlib import Path

from pydantic import ValidationError

from src.core.config import settings
from src.core.exceptions import DataNotFoundError, DataValidationError
from src.models.message import MessageDump

logger = logging.getLogger(__name__)


class MessageRepository:
    """Repository for accessing message dumps from tg_fetcher."""

    def __init__(self, data_path: Path | None = None) -> None:
        """Initialize message repository.

        Args:
            data_path: Path to tg_fetcher data directory
        """
        self._data_path = data_path or settings.tg_fetcher_data_path

    def _normalize_chat(self, chat: str) -> str:
        """Normalize chat identifier to match filesystem layout.

        The fetcher stores data in directories named without leading '@'.
        This method strips a leading '@' if present to ensure path resolution.

        Args:
            chat: Chat identifier, e.g. "@ru_python" or "ru_python".

        Returns:
            Normalized chat name without leading '@'.
        """
        return chat[1:] if chat.startswith("@") else chat

    def load_messages(self, chat: str, date: str) -> MessageDump:
        """Load messages for specific chat and date.

        Args:
            chat: Chat name (e.g., "ru_python")
            date: Date in YYYY-MM-DD format

        Returns:
            Message dump with all messages

        Raises:
            DataNotFoundError: If file not found
            DataValidationError: If data validation fails
        """
        normalized_chat = self._normalize_chat(chat)
        file_path = self._data_path / normalized_chat / f"{date}.json"

        logger.info(f"Loading messages from {file_path}")

        if not file_path.exists():
            raise DataNotFoundError(
                chat=chat,
                date=date,
                path=str(file_path),
            )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            message_dump = MessageDump.model_validate(data)

            logger.info(
                f"Loaded {len(message_dump.messages)} messages from "
                f"{message_dump.source_info.title} ({date})"
            )

            return message_dump

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            raise DataValidationError(f"Invalid JSON: {e}")

        except ValidationError as e:
            logger.error(f"Data validation failed for {file_path}: {e}")
            raise DataValidationError(f"Validation failed: {e}")

        except Exception as e:
            logger.error(f"Unexpected error loading {file_path}: {e}")
            raise

    def get_available_dates(self, chat: str) -> list[str]:
        """Get list of available dates for chat.

        Args:
            chat: Chat name

        Returns:
            List of dates in YYYY-MM-DD format
        """
        normalized_chat = self._normalize_chat(chat)
        chat_path = self._data_path / normalized_chat

        if not chat_path.exists():
            logger.warning(f"Chat directory not found: {chat_path}")
            return []

        dates = []
        for file_path in chat_path.glob("*.json"):
            # Extract date from filename (YYYY-MM-DD.json)
            date = file_path.stem
            dates.append(date)

        dates.sort(reverse=True)  # Most recent first

        logger.info(f"Found {len(dates)} dates for chat {chat}")

        return dates

    def get_available_chats(self) -> list[str]:
        """Get list of available chats.

        Returns:
            List of chat names
        """
        if not self._data_path.exists():
            logger.warning(f"Data path not found: {self._data_path}")
            return []

        chats = []
        for item in self._data_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                chats.append(item.name)

        chats.sort()

        logger.info(f"Found {len(chats)} chats")

        return chats
