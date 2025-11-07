"""Simple test script to verify GigaChat API connection."""

import asyncio
import logging
import sys
from pathlib import Path

from src.models.gigachat import GigaChatMessage
from src.services.gigachat_client import GigaChatClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def test_gigachat() -> None:
    """Test GigaChat API connection and basic completion."""

    logger.info("=== Testing GigaChat API ===\n")

    async with GigaChatClient() as client:
        # Test 1: Get available models
        try:
            logger.info("Test 1: Fetching available models...")
            models = await client.get_models()
            logger.info(f"✓ Success! Available models:")
            for model in models.data:
                logger.info(f"  - {model.id}")
            logger.info("")
        except Exception as e:
            logger.error(f"✗ Failed to fetch models: {e}")
            return

        # Test 2: Simple completion
        try:
            logger.info("Test 2: Sending test completion request...")

            messages = [
                GigaChatMessage(
                    role="system",
                    content="Ты - помощник для анализа технических дискуссий.",
                ),
                GigaChatMessage(
                    role="user", content="Привет! Кратко опиши, что ты умеешь делать."
                ),
            ]

            response = await client.complete(
                messages=messages, temperature=0.7, max_tokens=200
            )

            logger.info(f"✓ Success! Completion received:")
            logger.info(f"  Model: {response.model}")
            logger.info(f"  Tokens used: {response.usage.total_tokens}")
            logger.info(f"  Response:\n{response.choices[0].message.content}\n")

        except Exception as e:
            logger.error(f"✗ Failed to complete: {e}")
            return

    logger.info("=== All tests passed! ===")


if __name__ == "__main__":
    asyncio.run(test_gigachat())
