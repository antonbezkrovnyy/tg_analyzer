"""Test event subscriber by listening to Redis PubSub events.

Usage:
    python scripts/listen_events.py
"""

import asyncio
import logging
from typing import Any, Dict

from src.core.config import settings
from src.services.event_subscriber import EventSubscriber

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


async def handle_event(event_data: Dict[str, Any]) -> None:
    """Handle incoming event (for testing)."""
    logger.info(
        f"Received event: {event_data.get('event')}",
        extra={
            "chat": event_data.get("chat"),
            "date": event_data.get("date"),
            "message_count": event_data.get("message_count"),
            "file_path": event_data.get("file_path"),
        },
    )


async def main() -> None:
    """Listen to Redis events."""
    logger.info("Starting event listener (test script)...")
    logger.info(f"Redis URL: {settings.redis_url}")
    logger.info("Waiting for events on channel: tg_events")
    logger.info("Press Ctrl+C to exit\n")

    subscriber = EventSubscriber(
        redis_url=settings.redis_url,
        redis_password=settings.redis_password,
        event_handler=handle_event,
        worker_id="test-listener",
    )

    try:
        await subscriber.connect()
        await subscriber.listen()
    except KeyboardInterrupt:
        logger.info("\nStopping listener...")
    finally:
        await subscriber.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
