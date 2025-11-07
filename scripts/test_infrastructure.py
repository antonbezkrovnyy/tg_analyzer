"""Test new infrastructure: AnalysisRepository, PromptBuilder, AnalyzerService."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.repositories.analysis_repository import AnalysisRepository
from src.repositories.message_repository import MessageRepository
from src.services.analyzer_service import AnalyzerService
from src.services.gigachat_client import GigaChatClient
from src.services.prompt_builder import PromptBuilder

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def main():
    """Test the new infrastructure."""
    logger.info("Testing new infrastructure...\n")

    # Initialize all services
    logger.info("=== Initializing Services ===")

    message_repo = MessageRepository(
        data_path=Path(r"C:\Users\Мой компьютер\Desktop\python-tg\data")
    )
    logger.info("✓ MessageRepository")

    prompt_builder = PromptBuilder()
    logger.info("✓ PromptBuilder")

    analysis_repo = AnalysisRepository()
    logger.info("✓ AnalysisRepository")

    # Run analysis
    chat = "ru_python"
    date = "2025-11-05"

    async with GigaChatClient() as gigachat_client:
        logger.info("✓ GigaChatClient")

        analyzer = AnalyzerService(
            message_repo=message_repo,
            gigachat_client=gigachat_client,
            prompt_builder=prompt_builder,
            analysis_repo=analysis_repo,
            validate_links=True,
        )
        logger.info("✓ AnalyzerService\n")

        result, metadata = await analyzer.analyze(
            chat=chat, date=date, window_size=30, force=True
        )

    # Print summary (after context manager)
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    print(f"Saved to: output/{metadata.chat}/{metadata.date}.json")
    print(f"\nMetadata:")
    print(f"  Chat: {metadata.chat} (@{metadata.chat_username})")
    print(f"  Date: {metadata.date}")
    print(f"  Analyzed at: {metadata.analyzed_at}")
    print(f"  Messages: {metadata.analyzed_messages}/{metadata.total_messages}")
    print(f"  Tokens: {metadata.tokens_used}")
    print(f"  Model: {metadata.model}")
    print(f"  Latency: {metadata.latency_seconds:.2f}s")

    print(f"\nDiscussions: {len(result.discussions)}")
    for idx, discussion in enumerate(result.discussions, 1):
        print(f"\n  {idx}. {discussion.topic}")
        print(f"     Keywords: {', '.join(discussion.keywords[:5])}")
        print(f"     Participants: {', '.join(discussion.participants[:5])}")
        print(f"     Links: {len(discussion.message_links)} messages")

    print("\n" + "=" * 70)
    print("\n✅ Infrastructure test PASSED!")


if __name__ == "__main__":
    asyncio.run(main())
