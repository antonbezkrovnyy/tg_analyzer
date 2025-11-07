"""Service for orchestrating the full analysis pipeline."""

import json
import logging
import time
from datetime import datetime

from src.models.analysis import AnalysisMetadata, AnalysisResult
from src.models.gigachat import GigaChatMessage
from src.repositories.analysis_repository import AnalysisRepository
from src.repositories.message_repository import MessageRepository
from src.services.gigachat_client import GigaChatClient
from src.services.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class AnalyzerService:
    """Orchestrates the full analysis pipeline."""

    def __init__(
        self,
        message_repo: MessageRepository,
        gigachat_client: GigaChatClient,
        prompt_builder: PromptBuilder,
        analysis_repo: AnalysisRepository,
        validate_links: bool = True,
    ):
        """Initialize analyzer service.

        Args:
            message_repo: Repository for loading messages
            gigachat_client: GigaChat API client
            prompt_builder: Prompt builder service
            analysis_repo: Repository for saving results
            validate_links: Whether to validate message links (default: True)
        """
        self.message_repo = message_repo
        self.gigachat_client = gigachat_client
        self.prompt_builder = prompt_builder
        self.analysis_repo = analysis_repo
        self.validate_links = validate_links

    async def analyze(
        self,
        chat: str,
        date: str,
        window_size: int = 30,
        force: bool = False,
    ) -> tuple[AnalysisResult, AnalysisMetadata]:
        """Analyze chat for specific date.

        Args:
            chat: Chat name (e.g., "ru_python")
            date: Date in YYYY-MM-DD format
            window_size: Number of messages to analyze (default: 30)
            force: Overwrite existing analysis (default: False)

        Returns:
            Tuple of (AnalysisResult, AnalysisMetadata)

        Raises:
            FileNotFoundError: If message data doesn't exist
            ValueError: If analysis exists and force=False
        """
        logger.info(f"=== Analyzing {chat} - {date} ===\n")

        # Check if analysis already exists
        if self.analysis_repo.exists(chat, date) and not force:
            logger.info(f"Analysis already exists for {chat}/{date}")
            logger.info("Use force=True to overwrite\n")
            return self.analysis_repo.load(chat, date)

        # Step 1: Load messages
        logger.info("Step 1: Loading messages...")
        message_dump = self.message_repo.load_messages(chat, date)
        messages = message_dump.messages
        logger.info(f"✓ Loaded {len(messages)} messages\n")

        # Step 2: Build prompt
        logger.info("Step 2: Building prompt...")
        chat_username = message_dump.source_info.id.lstrip("@")
        prompt = self.prompt_builder.build(
            chat_name=message_dump.source_info.title,
            chat_username=chat_username,
            date=date,
            message_dump=message_dump,
            window_size=window_size,
        )
        logger.info(f"✓ Prompt built ({len(prompt)} characters)\n")

        # Step 3: Send to GigaChat
        logger.info("Step 3: Sending to GigaChat...")
        start_time = time.time()

        response = await self.gigachat_client.complete(
            messages=[GigaChatMessage(role="user", content=prompt)],
            temperature=0.5,
        )

        latency = time.time() - start_time
        logger.info("✓ Response received")
        logger.info(f"  Tokens used: {response.usage.total_tokens}")
        logger.info(f"  Model: {response.model}")
        logger.info(f"  Latency: {latency:.2f}s\n")

        # Step 4: Parse response
        logger.info("Step 4: Parsing response...")
        response_text = response.choices[0].message.content

        # Extract JSON from markdown code blocks if present
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        analysis_data = json.loads(response_text)
        result = AnalysisResult(discussions=analysis_data["discussions"])
        logger.info(f"✓ Parsed {len(result.discussions)} discussions\n")

        # Step 5: Validate links (if enabled)
        if self.validate_links:
            logger.info("Step 5: Validating message links...")
            message_ids = [msg.id for msg in messages[:window_size]]
            errors = self._validate_links(
                result.discussions, chat_username, message_ids
            )

            if errors:
                logger.warning(f"⚠ Found {len(errors)} link validation errors:")
                for error in errors:
                    logger.warning(f"  - {error}")
            else:
                logger.info("✓ All links valid\n")

        # Step 6: Save results
        logger.info("Step 6: Saving results...")
        metadata = AnalysisMetadata(
            chat=chat,
            chat_username=chat_username,
            date=date,
            analyzed_at=datetime.now(),
            total_messages=len(messages),
            analyzed_messages=min(window_size, len(messages)),
            tokens_used=response.usage.total_tokens,
            model=response.model,
            latency_seconds=latency,
        )

        saved_path = self.analysis_repo.save(chat, date, result, metadata)
        logger.info(f"✓ Results saved to {saved_path}\n")

        logger.info("=== Analysis Complete! ===\n")

        return result, metadata

    def _validate_links(
        self,
        discussions: list,
        chat_username: str,
        message_ids: list[int],
    ) -> list[str]:
        """Validate message_links in discussions.

        Args:
            discussions: List of discussions to validate
            chat_username: Expected chat username
            message_ids: Valid message IDs

        Returns:
            List of error messages (empty if all valid)
        """
        errors = []
        expected_prefix = f"https://t.me/{chat_username}/"

        for idx, discussion in enumerate(discussions, 1):
            topic = discussion.topic

            for link in discussion.message_links:
                # Check format
                if not link.startswith(expected_prefix):
                    errors.append(
                        f"{topic}: Wrong username in link: {link} "
                        f"(expected: {expected_prefix})"
                    )
                    continue

                # Extract message_id
                try:
                    msg_id = int(link.split("/")[-1])
                except (ValueError, IndexError):
                    errors.append(f"{topic}: Invalid link format: {link}")
                    continue

                # Check if message_id exists in input
                if msg_id not in message_ids:
                    errors.append(f"{topic}: Message {msg_id} not in analyzed messages")

        return errors
