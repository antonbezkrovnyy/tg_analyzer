"""Test script to analyze real message dump with GigaChat."""

import asyncio
import json
import logging
import sys
from pathlib import Path

from src.models.gigachat import GigaChatMessage
from src.repositories.message_repository import MessageRepository
from src.services.gigachat_client import GigaChatClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def build_simple_prompt(
    chat_name: str,
    chat_username: str,
    date: str,
    messages_json: str,
    message_count: int,
) -> str:
    """Build prompt for analysis from template file.

    Args:
        chat_name: Chat display name
        chat_username: Chat username (e.g., 'ru_python') for links
        date: Date
        messages_json: Formatted messages in JSON
        message_count: Total message count

    Returns:
        Prompt text with placeholders filled
    """
    from pathlib import Path

    # Load prompt template from config
    prompt_file = (
        Path(__file__).parent.parent / "config" / "prompts" / "analysis_prompt.txt"
    )

    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # Fill placeholders
    prompt = prompt_template.format(
        chat_name=chat_name,
        chat_username=chat_username,
        date=date,
        message_count=message_count,
        messages_json=messages_json,
    )

    return prompt


def format_messages(messages: list, senders: dict, max_messages: int = 50) -> str:
    """Format messages as JSON for prompt.

    Includes message ID, timestamp, sender, text, and reply_to for GigaChat
    to create accurate message links.

    Args:
        messages: List of message objects
        senders: Sender ID to name mapping
        max_messages: Maximum messages to include

    Returns:
        JSON string with message metadata
    """
    import json

    formatted_messages = []

    # Take first N messages (most recent if sorted)
    for msg in messages[:max_messages]:
        sender_name = senders.get(str(msg.sender_id), "Unknown")
        text = msg.text or "[no text]"

        # Truncate very long messages
        if len(text) > 500:
            text = text[:500] + "..."

        message_data = {
            "id": msg.id,
            "timestamp": msg.date.isoformat(),
            "sender": sender_name,
            "text": text,
            "reply_to": msg.reply_to_msg_id,
        }

        formatted_messages.append(message_data)

    return json.dumps(formatted_messages, ensure_ascii=False, indent=2)


async def test_analysis() -> None:
    """Test analysis of real message dump."""

    chat_name = "ru_python"
    date = "2025-11-05"

    logger.info(f"=== Analyzing {chat_name} - {date} ===\n")

    # 1. Load messages
    logger.info("Step 1: Loading messages...")
    repo = MessageRepository()

    try:
        message_dump = repo.load_messages(chat_name, date)
        logger.info(f"✓ Loaded {len(message_dump.messages)} messages\n")
    except Exception as e:
        logger.error(f"✗ Failed to load messages: {e}")
        return

    # Extract chat username from source_info for message links
    # source_info.id can be @username or channel_id, extract username part
    chat_username = message_dump.source_info.id
    if chat_username.startswith("@"):
        chat_username = chat_username[1:]  # Remove @ prefix

    # 2. Format messages for prompt (now JSON)
    logger.info("Step 2: Formatting messages...")
    messages_json = format_messages(
        message_dump.messages,
        message_dump.senders,
        max_messages=30,  # Start with 30 messages to not exceed token limit
    )
    logger.info(f"✓ Formatted {len(message_dump.messages[:30])} messages\n")

    # 3. Build prompt from template
    logger.info("Step 3: Building prompt...")
    prompt = build_simple_prompt(
        message_dump.source_info.title,  # Display name
        chat_username,  # Username for links
        date,
        messages_json,
        len(message_dump.messages),
    )
    logger.info(f"✓ Prompt built ({len(prompt)} characters)\n")

    # 4. Send to GigaChat
    logger.info("Step 4: Sending to GigaChat...")

    async with GigaChatClient() as client:
        try:
            response = await client.complete(
                messages=[GigaChatMessage(role="user", content=prompt)],
                temperature=0.5,  # Lower temperature for more consistent JSON
                max_tokens=2000,
            )

            logger.info(f"✓ Response received")
            logger.info(f"  Tokens used: {response.usage.total_tokens}")
            logger.info(f"  Model: {response.model}\n")

            # 5. Parse response
            logger.info("Step 5: Parsing response...")
            response_text = response.choices[0].message.content

            # Try to extract JSON from response
            try:
                # GigaChat might wrap JSON in markdown code blocks
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()

                analysis_data = json.loads(response_text)
                discussions_count = len(analysis_data.get("discussions", []))
                logger.info(f"✓ Parsed {discussions_count} discussions\n")

                # 6. Display results
                logger.info("=== ANALYSIS RESULTS ===\n")
                for i, discussion in enumerate(analysis_data.get("discussions", []), 1):
                    logger.info(f"Discussion {i}: {discussion.get('topic')}")
                    logger.info(
                        f"Keywords: {', '.join(discussion.get('keywords', []))}"
                    )
                    logger.info(
                        f"Participants: {', '.join(discussion.get('participants', []))}"
                    )
                    logger.info(f"Summary: {discussion.get('summary')}")
                    logger.info(f"Expert: {discussion.get('expert_comment')[:200]}...")
                    logger.info("")

                # Save to file
                output_file = Path("test_analysis_output.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "chat": chat_name,
                            "date": date,
                            "message_count": len(message_dump.messages),
                            "tokens_used": response.usage.total_tokens,
                            "analysis": analysis_data,
                        },
                        f,
                        ensure_ascii=False,
                        indent=2,
                    )

                logger.info(f"✓ Results saved to {output_file}")

            except json.JSONDecodeError as e:
                logger.error(f"✗ Failed to parse JSON response: {e}")
                logger.error(f"Raw response:\n{response_text}")

        except Exception as e:
            logger.error(f"✗ GigaChat request failed: {e}")
            return

    logger.info("\n=== Analysis Complete! ===")


if __name__ == "__main__":
    asyncio.run(test_analysis())
