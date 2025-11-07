"""CLI interface for running analysis."""

import asyncio
import logging
import sys
from pathlib import Path

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
    """Run analysis from command line."""
    # Parse arguments (simple version for now)
    if len(sys.argv) < 3:
        print(
            "Usage: python -m src.cli.analyze <chat> <date> [--force] [--window-size N]"
        )
        print("\nExample:")
        print("  python -m src.cli.analyze ru_python 2025-11-05")
        print(
            "  python -m src.cli.analyze ru_python 2025-11-05 --force --window-size 100"
        )
        sys.exit(1)

    chat = sys.argv[1]
    date = sys.argv[2]

    # Parse optional flags
    force = "--force" in sys.argv
    window_size = 30

    if "--window-size" in sys.argv:
        idx = sys.argv.index("--window-size")
        if idx + 1 < len(sys.argv):
            try:
                window_size = int(sys.argv[idx + 1])
            except ValueError:
                logger.error("Invalid window-size value")
                sys.exit(1)

    # Initialize services
    logger.info("Initializing services...")

    message_repo = MessageRepository(data_path=Path("../python-tg/data"))

    prompt_builder = PromptBuilder()

    analysis_repo = AnalysisRepository()

    # Run analysis with GigaChat context manager
    async with GigaChatClient() as gigachat_client:
        analyzer = AnalyzerService(
            message_repo=message_repo,
            gigachat_client=gigachat_client,
            prompt_builder=prompt_builder,
            analysis_repo=analysis_repo,
            validate_links=True,
        )

        try:
            result, metadata = await analyzer.analyze(
                chat=chat,
                date=date,
                window_size=window_size,
                force=force,
            )

            # Print summary
            print("\n" + "=" * 60)
            print("ANALYSIS SUMMARY")
            print("=" * 60)
            print(f"Chat: {metadata.chat}")
            print(f"Date: {metadata.date}")
            print(
                f"Analyzed: {metadata.analyzed_messages}/{metadata.total_messages} messages"
            )
            print(f"Tokens: {metadata.tokens_used}")
            print(f"Latency: {metadata.latency_seconds:.2f}s")
            print(f"Model: {metadata.model}")
            print(f"\nDiscussions found: {len(result.discussions)}")

            for idx, discussion in enumerate(result.discussions, 1):
                print(f"\n{idx}. {discussion.topic}")
                print(f"   Keywords: {', '.join(discussion.keywords)}")
                print(f"   Participants: {', '.join(discussion.participants)}")
                print(f"   Links: {len(discussion.message_links)} messages")

            print("\n" + "=" * 60)

        except FileNotFoundError as e:
            logger.error(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
