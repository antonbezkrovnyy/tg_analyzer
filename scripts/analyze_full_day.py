"""Analyze full day in batches to avoid GigaChat moderation."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.models.analysis import AnalysisMetadata, AnalysisResult, Discussion
from src.repositories.analysis_repository import AnalysisRepository
from src.repositories.message_repository import MessageRepository
from src.services.analyzer_service import AnalyzerService
from src.services.gigachat_client import GigaChatClient
from src.services.prompt_builder import PromptBuilder

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Analyze full day in batches."""
    if len(sys.argv) < 3:
        print("Usage: python analyze_full_day.py <chat> <date> [--batch-size N]")
        print(
            "Example: python analyze_full_day.py ru_python 2025-11-05 --batch-size 100"
        )
        sys.exit(1)

    chat = sys.argv[1]
    date = sys.argv[2]

    # Parse batch size
    batch_size = 100
    if "--batch-size" in sys.argv:
        idx = sys.argv.index("--batch-size")
        if idx + 1 < len(sys.argv):
            try:
                batch_size = int(sys.argv[idx + 1])
            except ValueError:
                logger.error("Invalid batch-size value")
                sys.exit(1)

    logger.info(f"Processing {chat} - {date} in batches of {batch_size}")

    # Initialize services
    message_repo = MessageRepository(data_path=Path("../python-tg/data"))
    prompt_builder = PromptBuilder()
    analysis_repo = AnalysisRepository()

    # Load all messages
    message_dump = message_repo.load_messages(chat, date)
    total_messages = len(message_dump.messages)
    logger.info(f"Loaded {total_messages} messages")

    # Extract username from URL (e.g., "https://t.me/ru_python" -> "ru_python")
    chat_username = message_dump.source_info.url.rstrip("/").split("/")[-1]
    chat_name = message_dump.source_info.title
    logger.info(f"Chat: {chat_name} (@{chat_username})")

    # Calculate batches
    num_batches = (total_messages + batch_size - 1) // batch_size
    logger.info(f"Will process in {num_batches} batches")

    all_discussions: list[Discussion] = []
    total_tokens = 0
    total_latency = 0.0

    async with GigaChatClient() as gigachat_client:
        analyzer = AnalyzerService(
            message_repo=message_repo,
            gigachat_client=gigachat_client,
            prompt_builder=prompt_builder,
            analysis_repo=analysis_repo,
            validate_links=True,
        )

        for batch_num in range(num_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_messages)

            logger.info(f"\n{'='*60}")
            logger.info(
                f"Batch {batch_num + 1}/{num_batches}: Messages {start_idx}-{end_idx}"
            )
            logger.info(f"{'='*60}")

            # Create temporary message dump for this batch
            batch_messages = message_dump.messages[start_idx:end_idx]
            batch_dump = type(message_dump)(
                version=message_dump.version,
                source_info=message_dump.source_info,
                messages=batch_messages,
                senders=message_dump.senders,
            )

            # Build prompt
            prompt = prompt_builder.build(
                chat_name=chat_name,
                chat_username=chat_username,
                date=date,
                message_dump=batch_dump,
                window_size=len(batch_messages),
            )

            # Send to GigaChat
            logger.info(f"Sending batch to GigaChat (prompt: {len(prompt)} chars)...")
            import time

            start_time = time.time()

            from src.models.gigachat import GigaChatMessage

            response = await gigachat_client.complete(
                messages=[GigaChatMessage(role="user", content=prompt)],
                temperature=0.5,
                max_tokens=8192,
            )

            latency = time.time() - start_time
            total_tokens += response.usage.total_tokens
            total_latency += latency

            logger.info(
                f"✓ Batch completed: {response.usage.total_tokens} tokens, {latency:.2f}s"
            )

            # Parse response
            response_text = response.choices[0].message.content

            if len(response_text) < 1000:
                logger.warning(f"Short response: {response_text}")
                continue

            # Extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            import json

            try:
                analysis_data = json.loads(response_text)
                batch_result = AnalysisResult(discussions=analysis_data["discussions"])

                logger.info(
                    f"✓ Parsed {len(batch_result.discussions)} discussions from batch"
                )

                # Add to combined list
                all_discussions.extend(batch_result.discussions)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from batch {batch_num + 1}: {e}")
                logger.error(f"Response text (last 200 chars): {response_text[-200:]}")
                logger.warning(f"Skipping batch {batch_num + 1}")
                continue

            # Small delay to avoid rate limiting
            await asyncio.sleep(1)

    # Save combined results
    logger.info(f"\n{'='*60}")
    logger.info(f"Saving combined results...")
    logger.info(f"{'='*60}")

    combined_result = AnalysisResult(discussions=all_discussions)
    metadata = AnalysisMetadata(
        chat=chat,
        chat_username=chat_username,
        date=date,
        total_messages=total_messages,
        analyzed_messages=total_messages,
        tokens_used=total_tokens,
        model="GigaChat:2.0.28.2",
        latency_seconds=total_latency,
    )

    analysis_repo.save(chat, date, combined_result, metadata)

    # Print summary
    print("\n" + "=" * 60)
    print("FULL DAY ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Chat: {metadata.chat}")
    print(f"Date: {metadata.date}")
    print(f"Total messages: {total_messages}")
    print(f"Batches processed: {num_batches}")
    print(f"Total tokens: {total_tokens}")
    print(f"Total latency: {total_latency:.2f}s")
    print(f"\nDiscussions found: {len(all_discussions)}")

    for idx, discussion in enumerate(all_discussions, 1):
        print(f"\n{idx}. {discussion.topic}")
        print(f"   Keywords: {', '.join(discussion.keywords)}")
        print(f"   Participants: {', '.join(discussion.participants)}")
        print(f"   Links: {len(discussion.message_links)} messages")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
