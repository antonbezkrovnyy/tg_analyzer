"""Redis event subscriber for listening to fetch completion events.

Subscribes to Redis PubSub channel 'tg_events' to receive notifications
when new Telegram messages are fetched by python-tg fetcher.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class EventSubscriber:
    """Subscribe to Redis PubSub events from telegram-fetcher.

    Listens for 'messages_fetched' events on 'tg_events' channel and
    triggers analysis callback when new data is available.
    """

    EVENTS_CHANNEL = "tg_events"

    def __init__(
        self,
        redis_url: str,
        redis_password: Optional[str] = None,
        event_handler: Optional[Callable] = None,
        worker_id: str = "analyzer-1",
    ):
        """Initialize event subscriber.

        Args:
            redis_url: Redis connection URL (redis://host:port)
            redis_password: Optional Redis password
            event_handler: Async function to handle events
            worker_id: Unique identifier for this worker (for logging)
        """
        self.redis_url = redis_url
        self.redis_password = redis_password
        self.event_handler = event_handler
        self.worker_id = worker_id
        self._redis_client: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._running = False

    async def connect(self) -> None:
        """Connect to Redis and subscribe to events channel."""
        try:
            self._redis_client = redis.from_url(
                self.redis_url,
                password=self.redis_password,
                decode_responses=True,
            )
            # Test connection
            await self._redis_client.ping()

            # Create PubSub instance
            self._pubsub = self._redis_client.pubsub()
            await self._pubsub.subscribe(self.EVENTS_CHANNEL)

            logger.info(
                f"Connected to Redis PubSub: {self.EVENTS_CHANNEL}",
                extra={
                    "channel": self.EVENTS_CHANNEL,
                    "redis_url": self.redis_url,
                    "worker_id": self.worker_id,
                },
            )
        except Exception as e:
            logger.error(
                f"Failed to connect to Redis: {e}",
                extra={"error": str(e), "redis_url": self.redis_url},
            )
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._pubsub:
            await self._pubsub.unsubscribe(self.EVENTS_CHANNEL)
            await self._pubsub.close()

        if self._redis_client:
            await self._redis_client.close()

        logger.info(
            "Disconnected from Redis",
            extra={"worker_id": self.worker_id},
        )

    async def listen(self) -> None:
        """Listen for events from Redis PubSub channel.

        Processes events with type 'messages_fetched' from telegram-fetcher.

        Event format (JSON):
        {
            "event": "messages_fetched",
            "chat": "ru_python",
            "date": "2025-11-08",
            "message_count": 580,
            "file_path": "/data/ru_python/2025-11-08.json",
            "duration_seconds": 15.3,
            "timestamp": "2025-11-08T10:30:00Z",
            "service": "tg_fetcher"
        }
        """
        if not self._pubsub:
            raise RuntimeError("Not connected to Redis. Call connect() first.")

        self._running = True
        logger.info(
            "Started listening for events (PubSub pattern)...",
            extra={
                "worker_id": self.worker_id,
                "channel": self.EVENTS_CHANNEL,
            },
        )

        try:
            async for message in self._pubsub.listen():
                if not self._running:
                    break

                # Skip subscription confirmations
                if message["type"] != "message":
                    continue

                await self._handle_event(message["data"])

        except asyncio.CancelledError:
            logger.info(
                "Listen loop cancelled",
                extra={"worker_id": self.worker_id},
            )
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, stopping...")
        except Exception as e:
            logger.error(f"Error in listen loop: {e}", exc_info=True)
        finally:
            self._running = False

    async def _handle_event(self, event_json: str) -> None:
        """Handle incoming Redis event.

        Args:
            event_json: JSON string with event data
        """
        try:
            # Parse event
            event_data = json.loads(event_json)
            event_type = event_data.get("event")

            logger.info(
                "Received event",
                extra={
                    "event": event_type,
                    "chat": event_data.get("chat"),
                    "date": event_data.get("date"),
                    "message_count": event_data.get("message_count"),
                    "worker_id": self.worker_id,
                },
            )

            # Process messages_fetched event
            if event_type == "messages_fetched":
                if self.event_handler:
                    await self.event_handler(event_data)
                else:
                    logger.warning("No event handler registered")

            elif event_type == "fetch_failed":
                chat = event_data.get("chat")
                date = event_data.get("date")
                logger.warning(
                    f"Fetch failed for {chat}/{date}",
                    extra={
                        "error": event_data.get("error"),
                        "event_data": event_data,
                    },
                )

            else:
                logger.warning(
                    f"Unknown event type: {event_type}",
                    extra={"event_data": event_data},
                )

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse event JSON: {e}",
                extra={"event_json": event_json},
            )
        except Exception as e:
            logger.error(
                f"Error handling event: {e}",
                extra={"event_json": event_json},
                exc_info=True,
            )

    def stop(self) -> None:
        """Stop listening for events."""
        self._running = False
        logger.info("Stopping event subscriber...")


def create_fetch_event(
    chat: str,
    date: str,
    message_count: int,
    file_path: str,
    duration_seconds: float,
) -> dict[str, Any]:
    """Create a fetch event dict for testing.

    Args:
        chat: Chat name
        date: Date in YYYY-MM-DD format
        message_count: Number of messages fetched
        file_path: Path to JSON file
        duration_seconds: Fetch duration

    Returns:
        Event dict ready to be published to Redis
    """
    return {
        "event": "messages_fetched",
        "chat": chat,
        "date": date,
        "message_count": message_count,
        "file_path": file_path,
        "duration_seconds": duration_seconds,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "tg_fetcher",
    }
