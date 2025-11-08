"""Telegram Analyzer Daemon.

Continuous service that listens for fetch completion events from
telegram-fetcher and automatically triggers analysis.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.core.config import settings
from src.repositories.analysis_repository import AnalysisRepository
from src.repositories.message_repository import MessageRepository
from src.services.analyzer_service import AnalyzerService
from src.services.event_subscriber import EventSubscriber
from src.services.gigachat_client import GigaChatClient
from src.services.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class AnalyzerDaemon:
    """Daemon process for automatic Telegram message analysis.

    Subscribes to Redis PubSub events from telegram-fetcher and
    triggers analysis when new messages are fetched.
    """

    def __init__(self, worker_id: str = "analyzer-1"):
        """Initialize analyzer daemon.

        Args:
            worker_id: Unique identifier for this worker instance
        """
        self.worker_id = worker_id
        self.event_subscriber: Optional[EventSubscriber] = None
        self.analyzer_service: Optional[AnalyzerService] = None
        self.gigachat_client: Optional[GigaChatClient] = None
        self._shutdown_event = asyncio.Event()

    async def setup(self) -> None:
        """Initialize services and connections."""
        logger.info(
            f"Starting Analyzer Daemon [Worker: {self.worker_id}]",
            extra={"worker_id": self.worker_id},
        )

        # Initialize repositories
        message_repo = MessageRepository(data_path=Path(settings.tg_fetcher_data_path))
        prompt_builder = PromptBuilder()
        analysis_repo = AnalysisRepository()

        # Initialize GigaChat client
        self.gigachat_client = GigaChatClient()
        await self.gigachat_client.__aenter__()

        # Initialize AnalyzerService
        self.analyzer_service = AnalyzerService(
            message_repo=message_repo,
            gigachat_client=self.gigachat_client,
            prompt_builder=prompt_builder,
            analysis_repo=analysis_repo,
            validate_links=True,
        )

        # Initialize EventSubscriber
        self.event_subscriber = EventSubscriber(
            redis_url=settings.redis_url,
            redis_password=settings.redis_password,
            event_handler=self._handle_fetch_event,
            worker_id=self.worker_id,
        )

        # Connect to Redis
        await self.event_subscriber.connect()

        logger.info(
            "Analyzer daemon initialized successfully",
            extra={"worker_id": self.worker_id},
        )

    async def _handle_fetch_event(self, event_data: Dict[str, Any]) -> None:
        """Handle messages_fetched event by triggering analysis.

        Args:
            event_data: Event data from Redis PubSub
                {
                    "event": "messages_fetched",
                    "chat": "ru_python",
                    "date": "2025-11-08",
                    "message_count": 580,
                    "file_path": "/data/ru_python/2025-11-08.json",
                    "timestamp": "2025-11-08T10:30:00Z"
                }
        """
        chat = event_data.get("chat")
        date = event_data.get("date")
        message_count = event_data.get("message_count", 0)

        if not chat or not date:
            logger.error(
                "Invalid event data: missing chat or date",
                extra={"event_data": event_data},
            )
            return

        logger.info(
            f"Triggering analysis for {chat}/{date} " f"({message_count} messages)",
            extra={
                "chat": chat,
                "date": date,
                "message_count": message_count,
                "worker_id": self.worker_id,
            },
        )

        try:
            start_time = datetime.utcnow()

            # Run analysis
            if self.analyzer_service is None:
                raise RuntimeError("AnalyzerService not initialized")

            result, metadata = await self.analyzer_service.analyze(
                chat=chat,
                date=date,
                window_size=settings.window_size,
            )

            duration = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                f"Analysis completed successfully for {chat}/{date}",
                extra={
                    "chat": chat,
                    "date": date,
                    "discussions": len(result.discussions),
                    "tokens_used": metadata.tokens_used,
                    "duration_seconds": round(duration, 2),
                    "worker_id": self.worker_id,
                },
            )

        except FileNotFoundError as e:
            logger.error(
                f"Messages file not found for {chat}/{date}: {e}",
                extra={"chat": chat, "date": date, "error": str(e)},
            )
        except Exception as e:
            logger.error(
                f"Analysis failed for {chat}/{date}: {e}",
                extra={"chat": chat, "date": date, "error": str(e)},
                exc_info=True,
            )

    async def run(self) -> None:
        """Run daemon main loop (listen for events)."""
        if self.event_subscriber is None:
            raise RuntimeError("Daemon not set up. Call setup() first.")

        try:
            # Start listening for events
            await self.event_subscriber.listen()
        except asyncio.CancelledError:
            logger.info("Daemon loop cancelled")
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info(
            "Shutting down Analyzer Daemon...",
            extra={"worker_id": self.worker_id},
        )

        # Stop event subscriber
        if self.event_subscriber:
            self.event_subscriber.stop()
            await self.event_subscriber.disconnect()

        # Close GigaChat client
        if self.gigachat_client:
            await self.gigachat_client.__aexit__(None, None, None)

        logger.info(
            "Analyzer Daemon stopped",
            extra={"worker_id": self.worker_id},
        )

        self._shutdown_event.set()


async def main() -> None:
    """Entry point for daemon process."""
    # Get worker_id from environment or use default
    import os

    worker_id = os.getenv("WORKER_ID", "analyzer-1")

    # Create daemon
    daemon = AnalyzerDaemon(worker_id=worker_id)

    # Setup signal handlers
    loop = asyncio.get_running_loop()

    def signal_handler(signum: int) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(daemon.shutdown())

    # Register signal handlers (SIGTERM, SIGINT)
    try:
        loop.add_signal_handler(signal.SIGTERM, lambda: signal_handler(signal.SIGTERM))
        loop.add_signal_handler(signal.SIGINT, lambda: signal_handler(signal.SIGINT))
    except NotImplementedError:
        # Windows doesn't support add_signal_handler
        signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s))
        signal.signal(signal.SIGINT, lambda s, f: signal_handler(s))

    # Initialize and run
    try:
        await daemon.setup()
        await daemon.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        await daemon.shutdown()
    except Exception as e:
        logger.error(f"Daemon crashed: {e}", exc_info=True)
        await daemon.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )

    # Run daemon
    asyncio.run(main())
