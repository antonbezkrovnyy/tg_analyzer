"""Service for orchestrating the full analysis pipeline."""

import json
import logging
import time
from datetime import datetime

from src.models.analysis import AnalysisMetadata, AnalysisResult
from src.observability.logging_config import get_logger
from src.utils.correlation import get_correlation_id
from src.models.gigachat import GigaChatMessage
from src.repositories.analysis_repository import AnalysisRepository
from src.repositories.message_repository import MessageRepository
from src.services.gigachat_client import GigaChatClient
from src.services.prompt_builder import PromptBuilder

logger = get_logger(__name__)


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
        batch_size: int | None = 100,
    ) -> tuple[AnalysisResult, AnalysisMetadata]:
        """Analyze chat for specific date.

        Args:
            chat: Chat name (e.g., "ru_python")
            date: Date in YYYY-MM-DD format
            window_size: Number of messages to analyze (legacy single window mode)
            force: Overwrite existing analysis (default: False)
            batch_size: If provided (default 100), analyze ALL messages in batches of this size

        Returns:
            Tuple of (AnalysisResult, AnalysisMetadata)

        Raises:
            FileNotFoundError: If message data doesn't exist
            ValueError: If analysis exists and force=False
        """
        logger.info(
            "Analyzing",
            extra={"chat": chat, "date": date, "correlation_id": get_correlation_id()},
        )

        # Check if analysis already exists
        if self.analysis_repo.exists(chat, date) and not force:
            logger.info(
                "Analysis already exists",
                extra={"chat": chat, "date": date, "correlation_id": get_correlation_id()},
            )
            logger.info(
                "Use force=True to overwrite",
                extra={"correlation_id": get_correlation_id()},
            )
            return self.analysis_repo.load(chat, date)

        # Step 1: Load messages
        logger.info(
            "Step 1: Loading messages...",
            extra={"correlation_id": get_correlation_id()},
        )
        message_dump = self.message_repo.load_messages(chat, date)
        messages = message_dump.messages
        logger.info(
            "Messages loaded",
            extra={"count": len(messages), "correlation_id": get_correlation_id()},
        )

        chat_username = message_dump.source_info.id.lstrip("@")

        # Step 2–4: Build prompts and get responses (batched or legacy single window)
        all_discussions: list = []
        total_tokens_used: int = 0
        total_latency: float = 0.0

        if batch_size:
            logger.info(
                "Step 2: Building prompts for batches...",
                extra={"batch_size": batch_size, "correlation_id": get_correlation_id()},
            )
            # Chunk messages
            msgs = messages
            chunks = [msgs[i : i + batch_size] for i in range(0, len(msgs), batch_size)]

            for idx, chunk in enumerate(chunks, start=1):
                prompt = self.prompt_builder.build_for_subset(
                    chat_name=message_dump.source_info.title,
                    chat_username=chat_username,
                    date=date,
                    message_dump=message_dump,
                    messages_subset=chunk,
                )
                logger.info(
                    "Prompt built",
                    extra={
                        "length": len(prompt),
                        "batch_index": idx,
                        "batch_count": len(chunks),
                        "correlation_id": get_correlation_id(),
                    },
                )

                # Step 3: Send to GigaChat for this batch
                logger.info(
                    "Step 3: Sending to GigaChat (batch)...",
                    extra={"batch_index": idx, "correlation_id": get_correlation_id()},
                )
                start_time = time.time()
                response = await self.gigachat_client.complete(
                    messages=[GigaChatMessage(role="user", content=prompt)],
                    temperature=0.3,
                    max_tokens=8192,
                )
                latency = time.time() - start_time
                total_latency += latency
                total_tokens_used += response.usage.total_tokens
                logger.info(
                    "Response received",
                    extra={
                        "tokens_used": response.usage.total_tokens,
                        "model": response.model,
                        "latency_seconds": round(latency, 2),
                        "batch_index": idx,
                        "correlation_id": get_correlation_id(),
                    },
                )

                # Step 4: Parse response
                logger.info(
                    "Step 4: Parsing response (batch)...",
                    extra={"batch_index": idx, "correlation_id": get_correlation_id()},
                )
                response_text = response.choices[0].message.content
                if len(response_text) < 1000:
                    logger.warning(
                        "Short response detected",
                        extra={"preview": response_text[:500], "batch_index": idx, "correlation_id": get_correlation_id()},
                    )
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()

                try:
                    analysis_data = json.loads(response_text)
                    batch_discussions = analysis_data.get("discussions", [])
                except Exception as e:
                    logger.error(
                        "Failed to parse JSON for batch",
                        extra={"error": str(e), "batch_index": idx, "correlation_id": get_correlation_id()},
                    )
                    batch_discussions = []

                all_discussions.extend(batch_discussions)

            # Merge discussions across batches
            merged_discussions = self._merge_discussions(all_discussions)
            result = AnalysisResult(discussions=merged_discussions)
            logger.info(
                "Parsed discussions",
                extra={"count": len(result.discussions), "correlation_id": get_correlation_id()},
            )
        else:
            # Legacy single-window behavior
            logger.info(
                "Step 2: Building prompt...",
                extra={"correlation_id": get_correlation_id()},
            )
            prompt = self.prompt_builder.build(
                chat_name=message_dump.source_info.title,
                chat_username=chat_username,
                date=date,
                message_dump=message_dump,
                window_size=window_size,
            )
            logger.info(
                "Prompt built",
                extra={"length": len(prompt), "correlation_id": get_correlation_id()},
            )

            logger.info(
                "Step 3: Sending to GigaChat...",
                extra={"correlation_id": get_correlation_id()},
            )
            start_time = time.time()
            response = await self.gigachat_client.complete(
                messages=[GigaChatMessage(role="user", content=prompt)],
                temperature=0.5,
                max_tokens=8192,
            )
            latency = time.time() - start_time
            total_latency = latency
            total_tokens_used = response.usage.total_tokens
            logger.info(
                "Response received",
                extra={
                    "tokens_used": response.usage.total_tokens,
                    "model": response.model,
                    "latency_seconds": round(latency, 2),
                    "correlation_id": get_correlation_id(),
                },
            )

            logger.info(
                "Step 4: Parsing response...",
                extra={"correlation_id": get_correlation_id()},
            )
            response_text = response.choices[0].message.content
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
            logger.info(
                "Parsed discussions",
                extra={"count": len(result.discussions), "correlation_id": get_correlation_id()},
            )

        # Step 4.5: Enrich discussions with calculated metrics
        logger.info(
            "Step 4.5: Calculating metrics...",
            extra={"correlation_id": get_correlation_id()},
        )
        self._enrich_discussions(result.discussions)
        logger.info(
            "Metrics calculated",
            extra={"correlation_id": get_correlation_id()},
        )

        # Step 5: Validate links (if enabled)
        if self.validate_links:
            logger.info("Step 5: Validating message links...")
            message_ids = [msg.id for msg in messages]
            errors = self._validate_links(
                result.discussions, chat_username, message_ids
            )

            if errors:
                logger.warning(f"⚠ Found {len(errors)} link validation errors:")
                for error in errors:
                    logger.warning(f"  - {error}")
            else:
                logger.info("All links valid", extra={"correlation_id": get_correlation_id()})

        # Step 6: Save results
        logger.info(
            "Step 6: Saving results...",
            extra={"correlation_id": get_correlation_id()},
        )

        # Generate discussion statistics
        discussion_stats = self._calculate_stats(result.discussions)

        metadata = AnalysisMetadata(
            chat=chat,
            chat_username=chat_username,
            date=date,
            analyzed_at=datetime.now(),
            total_messages=len(messages),
            analyzed_messages=len(messages),
            tokens_used=total_tokens_used,
            model=response.model if not isinstance(result, list) else "multi-batch",
            latency_seconds=total_latency,
            discussion_stats=discussion_stats,
        )

        saved_path = self.analysis_repo.save(chat, date, result, metadata)
        logger.info(
            "Results saved",
            extra={"path": str(saved_path), "correlation_id": get_correlation_id()},
        )

        logger.info(
            "Analysis complete",
            extra={"correlation_id": get_correlation_id()},
        )

        return result, metadata

    def _merge_discussions(self, discussions: list) -> list:
        """Merge discussions from multiple batches.

        Strategy: key by normalized topic; union fields; pick higher practical_value.

        Args:
            discussions: list of dicts from all batches

        Returns:
            Merged list of dicts
        """
        if not discussions:
            return []

        def norm_topic(s: str) -> str:
            return (s or "").strip().lower()

        merged: dict[str, dict] = {}

        for disc in discussions:
            if not isinstance(disc, dict):
                # If model object, convert via __dict__ best-effort
                try:
                    disc = dict(disc)
                except Exception:
                    continue
            t = norm_topic(disc.get("topic", ""))
            if not t:
                # skip invalid
                continue
            if t not in merged:
                # shallow copy to avoid mutating original
                merged[t] = {
                    "topic": disc.get("topic"),
                    "keywords": list(dict.fromkeys(disc.get("keywords", [])))[:5],
                    "participants": list(dict.fromkeys(disc.get("participants", []))),
                    "summary": disc.get("summary", ""),
                    "expert_comment": disc.get("expert_comment", {}),
                    "message_links": list(dict.fromkeys(disc.get("message_links", []))),
                    "complexity": disc.get("complexity", 2),
                    "sentiment": disc.get("sentiment", "neutral"),
                    "practical_value": disc.get("practical_value", 5),
                }
            else:
                dst = merged[t]
                # union fields
                dst["keywords"] = list(
                    dict.fromkeys((dst.get("keywords", []) or []) + (disc.get("keywords", []) or []))
                )[:5]
                dst["participants"] = list(
                    dict.fromkeys((dst.get("participants", []) or []) + (disc.get("participants", []) or []))
                )
                dst["message_links"] = list(
                    dict.fromkeys((dst.get("message_links", []) or []) + (disc.get("message_links", []) or []))
                )
                # pick higher practical_value; update summary/expert_comment accordingly
                try:
                    pv_dst = int(dst.get("practical_value", 0))
                    pv_src = int(disc.get("practical_value", 0))
                except Exception:
                    pv_dst = 0
                    pv_src = 0
                if pv_src > pv_dst:
                    dst["summary"] = disc.get("summary", dst.get("summary", ""))
                    dst["expert_comment"] = disc.get("expert_comment", dst.get("expert_comment", {}))
                    dst["practical_value"] = pv_src
                # complexity = max
                try:
                    dst["complexity"] = max(int(dst.get("complexity", 0)), int(disc.get("complexity", 0)))
                except Exception:
                    pass
                # sentiment: simple majority heuristic skipped; keep existing

        return list(merged.values())

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

    def _enrich_discussions(self, discussions: list) -> None:
        """Calculate and set automatic metrics for discussions.

        Args:
            discussions: List of Discussion objects to enrich
        """
        for disc in discussions:
            # Ensure it's a Discussion object (not dict)
            if isinstance(disc, dict):
                continue

            # Calculate participant_count and message_count
            disc.participant_count = len(disc.participants)
            disc.message_count = len(disc.message_links)

            # Calculate priority based on metrics
            disc.priority = self._calculate_priority(
                disc.participant_count,
                disc.message_count,
                disc.practical_value,
            )

    def _calculate_priority(
        self, participant_count: int, message_count: int, practical_value: int
    ) -> str:
        """Calculate discussion priority based on metrics.

        Args:
            participant_count: Number of participants
            message_count: Number of messages
            practical_value: Practical value (1-10)

        Returns:
            Priority level: "high", "medium", or "low"
        """
        if participant_count >= 5 or message_count >= 10 or practical_value >= 8:
            return "high"
        elif participant_count >= 3 or message_count >= 5 or practical_value >= 5:
            return "medium"
        else:
            return "low"

    def _calculate_stats(self, discussions: list) -> dict:
        """Generate statistics about discussions.

        Args:
            discussions: List of Discussion objects

        Returns:
            Dictionary with statistics
        """
        from collections import Counter
        from statistics import mean

        if not discussions:
            return {}

        # Extract all keywords
        all_keywords = []
        for disc in discussions:
            all_keywords.extend(disc.keywords)

        # Count by priority
        priority_counts = Counter(disc.priority for disc in discussions)

        # Count by complexity
        complexity_counts = Counter(str(disc.complexity) for disc in discussions)

        # Count by sentiment
        sentiment_counts = Counter(disc.sentiment for disc in discussions)

        # Calculate averages
        avg_participants = mean(disc.participant_count for disc in discussions)
        avg_messages = mean(disc.message_count for disc in discussions)
        avg_complexity = mean(disc.complexity for disc in discussions)
        avg_practical_value = mean(disc.practical_value for disc in discussions)

        # Top keywords
        keyword_counter = Counter(all_keywords)
        top_keywords = [kw for kw, _ in keyword_counter.most_common(10)]

        return {
            "total_discussions": len(discussions),
            "by_priority": dict(priority_counts),
            "by_complexity": dict(complexity_counts),
            "by_sentiment": dict(sentiment_counts),
            "avg_participants": round(avg_participants, 1),
            "avg_messages": round(avg_messages, 1),
            "avg_complexity": round(avg_complexity, 1),
            "avg_practical_value": round(avg_practical_value, 1),
            "top_keywords": top_keywords,
        }
