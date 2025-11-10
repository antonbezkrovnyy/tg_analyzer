"""Repository for saving and loading analysis results."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models.analysis import AnalysisMetadata, AnalysisResult
from src.core.config import settings


class AnalysisRepository:
    """Repository for managing analysis results in output directory."""

    def __init__(self, output_dir: Path | None = None):
        """Initialize repository.

        Args:
            output_dir: Base directory for output files. If None, uses
                settings.output_path (supports container mount like "/output").
        """
        # Use configured output path when not explicitly provided
        self.output_dir = Path(output_dir or settings.output_path)

    def _normalize_chat(self, chat: str) -> str:
        """Normalize chat identifier to a filesystem-friendly folder name.

        Strips a leading '@' to align with fetcher data layout and historical
        output structure (e.g., "@ru_python" -> "ru_python").

        Args:
            chat: Chat identifier from events or inputs

        Returns:
            Normalized chat directory name
        """
        return chat[1:] if chat.startswith("@") else chat

    def save(
        self,
        chat: str,
        date: str,
        result: AnalysisResult,
        metadata: AnalysisMetadata,
    ) -> Path:
        """Save analysis result to output/{chat}/{date}.json

        Args:
            chat: Chat name (e.g., "ru_python")
            date: Date in YYYY-MM-DD format
            result: Analysis result with discussions
            metadata: Metadata about analysis (tokens, latency, etc.)

        Returns:
            Path to saved file

        Raises:
            ValueError: If chat or date are invalid
        """
        if not chat or not date:
            raise ValueError("Chat and date must be non-empty")

        # Create directory structure (normalized)
        normalized_chat = self._normalize_chat(chat)
        chat_dir = self.output_dir / normalized_chat
        chat_dir.mkdir(parents=True, exist_ok=True)

        # Prepare data
        data = {
            "metadata": metadata.model_dump(),
            "discussions": [d.model_dump() for d in result.discussions],
        }

        # Save to file
        file_path = chat_dir / f"{date}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        return file_path

    def load(self, chat: str, date: str) -> tuple[AnalysisResult, AnalysisMetadata]:
        """Load existing analysis from file.

        Args:
            chat: Chat name
            date: Date in YYYY-MM-DD format

        Returns:
            Tuple of (AnalysisResult, AnalysisMetadata)

        Raises:
            FileNotFoundError: If analysis doesn't exist
        """
        normalized_chat = self._normalize_chat(chat)
        file_path = self.output_dir / normalized_chat / f"{date}.json"

        if not file_path.exists():
            raise FileNotFoundError(f"Analysis not found: {chat}/{date}.json")

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        metadata = AnalysisMetadata(**data["metadata"])
        result = AnalysisResult(discussions=data["discussions"])

        return result, metadata

    def exists(self, chat: str, date: str) -> bool:
        """Check if analysis already exists.

        Args:
            chat: Chat name
            date: Date in YYYY-MM-DD format

        Returns:
            True if analysis file exists
        """
        normalized_chat = self._normalize_chat(chat)
        file_path = self.output_dir / normalized_chat / f"{date}.json"
        return file_path.exists()

    def list_dates(self, chat: str) -> list[str]:
        """List all analyzed dates for chat.

        Args:
            chat: Chat name

        Returns:
            List of dates in YYYY-MM-DD format, sorted
        """
        normalized_chat = self._normalize_chat(chat)
        chat_dir = self.output_dir / normalized_chat

        if not chat_dir.exists():
            return []

        # Find all .json files
        json_files = chat_dir.glob("*.json")

        # Extract dates (filename without .json)
        dates = [f.stem for f in json_files]

        return sorted(dates)

    def list_chats(self) -> list[str]:
        """List all chats with analysis.

        Returns:
            List of chat names, sorted
        """
        if not self.output_dir.exists():
            return []

        # Find all directories
        chat_dirs = [d for d in self.output_dir.iterdir() if d.is_dir()]

        return sorted([d.name for d in chat_dirs])

    def delete(self, chat: str, date: str) -> bool:
        """Delete analysis for specific date.

        Args:
            chat: Chat name
            date: Date in YYYY-MM-DD format

        Returns:
            True if file was deleted, False if didn't exist
        """
        normalized_chat = self._normalize_chat(chat)
        file_path = self.output_dir / normalized_chat / f"{date}.json"

        if not file_path.exists():
            return False

        file_path.unlink()
        return True

    def get_latest(
        self, chat: str
    ) -> Optional[tuple[str, AnalysisResult, AnalysisMetadata]]:
        """Get most recent analysis for chat.

        Args:
            chat: Chat name

        Returns:
            Tuple of (date, AnalysisResult, AnalysisMetadata) or None if no analyses
        """
        dates = self.list_dates(chat)

        if not dates:
            return None

        latest_date = dates[-1]  # Sorted, so last is most recent
        result, metadata = self.load(chat, latest_date)

        return latest_date, result, metadata
