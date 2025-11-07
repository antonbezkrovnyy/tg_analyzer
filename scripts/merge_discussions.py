"""Merge similar discussions using GigaChat."""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.analysis import AnalysisResult, Discussion
from src.models.gigachat import GigaChatMessage
from src.repositories.analysis_repository import AnalysisRepository
from src.services.gigachat_client import GigaChatClient

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


MERGE_PROMPT_TEMPLATE = """Ты - эксперт по анализу Telegram чатов.

У меня есть список дискуссий, извлечённых из одного дня чата. Некоторые из них могут быть:
- Дубликатами (одна и та же тема, найденная в разных батчах сообщений)
- Продолжением одной дискуссии (тема началась в одном батче, продолжилась в другом)
- Связанными темами (можно объединить в одну более крупную дискуссию)

**Твоя задача:**
1. Проанализируй все дискуссии
2. Объедини дубликаты и связанные темы
3. Для объединённых дискуссий:
   - Создай общий topic (краткое название)
   - Объедини keywords (уникальные)
   - Объедини participants (уникальные)
   - Объедини message_links (все ссылки)
   - Создай новый summary (общее описание)
   - Создай новый expert_comment (экспертная оценка всей темы)

**Входные дискуссии:**

{discussions_json}

**Выходной формат:**

Верни JSON с объединёнными дискуссиями в том же формате:

```json
{{
  "discussions": [
    {{
      "topic": "...",
      "keywords": [...],
      "participants": [...],
      "summary": "...",
      "expert_comment": "...",
      "message_links": [...]
    }}
  ]
}}
```

**Важно:**
- Если дискуссии явно разные - оставь их отдельно
- Если сомневаешься - лучше объединить
- Сохраняй все message_links из всех объединённых дискуссий
- В summary укажи, что это объединённая дискуссия из N частей (если актуально)
"""


async def main() -> None:
    """Merge similar discussions in analysis result."""
    if len(sys.argv) < 3:
        print("Usage: python merge_discussions.py <chat> <date>")
        print("Example: python merge_discussions.py ru_python 2025-11-05")
        sys.exit(1)

    chat = sys.argv[1]
    date = sys.argv[2]

    logger.info(f"Merging discussions for {chat} - {date}")

    # Load existing analysis
    analysis_repo = AnalysisRepository()

    if not analysis_repo.exists(chat, date):
        logger.error(f"No analysis found for {chat} - {date}")
        sys.exit(1)

    result, metadata = analysis_repo.load(chat, date)
    original_count = len(result.discussions)
    logger.info(f"Loaded {original_count} discussions")

    # If too many discussions, merge in batches
    MERGE_BATCH_SIZE = 10  # Merge 10 discussions at a time
    all_merged: list[Discussion] = []

    if original_count <= MERGE_BATCH_SIZE:
        # Small enough - merge all at once
        batches = [result.discussions]
    else:
        # Split into batches
        batches = [
            result.discussions[i : i + MERGE_BATCH_SIZE]
            for i in range(0, original_count, MERGE_BATCH_SIZE)
        ]
        logger.info(f"Splitting into {len(batches)} merge batches")

    async with GigaChatClient() as client:
        for batch_idx, batch in enumerate(batches, 1):
            logger.info(
                f"\nMerging batch {batch_idx}/{len(batches)} ({len(batch)} discussions)..."
            )

            # Convert to JSON for prompt
            discussions_json = json.dumps(
                [d.model_dump() for d in batch], indent=2, ensure_ascii=False
            )

            # Build prompt
            prompt = MERGE_PROMPT_TEMPLATE.format(discussions_json=discussions_json)
            logger.info(f"Prompt size: {len(prompt)} characters")

            # Send to GigaChat
            import time

            start_time = time.time()

            response = await client.complete(
                messages=[GigaChatMessage(role="user", content=prompt)],
                temperature=0.3,  # Lower temp for more deterministic merging
                max_tokens=16384,  # Should be enough for 10 discussions
            )

            latency = time.time() - start_time
            logger.info(
                f"✓ Response received: {response.usage.total_tokens} tokens, {latency:.2f}s"
            )

            # Parse response
            response_text = response.choices[0].message.content

            if len(response_text) < 100:
                logger.error(f"Short response: {response_text}")
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

            try:
                merged_data = json.loads(response_text)
                batch_merged = AnalysisResult(discussions=merged_data["discussions"])
                all_merged.extend(batch_merged.discussions)
                logger.info(
                    f"✓ Batch merged: {len(batch)} → {len(batch_merged.discussions)} discussions"
                )

                # Update metadata
                metadata.tokens_used += response.usage.total_tokens
                metadata.latency_seconds += latency
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
                logger.error(f"Response preview: {response_text[:500]}")
                # Keep original discussions if merge fails
                all_merged.extend(batch)

            # Small delay
            await asyncio.sleep(1)

    merged_result = AnalysisResult(discussions=all_merged)
    merged_count = len(merged_result.discussions)
    logger.info(f"✓ Total merged: {original_count} → {merged_count} discussions")

    # Save merged result
    analysis_repo.save(chat, date, merged_result, metadata)
    logger.info(f"✓ Saved merged result to output/{chat}/{date}.json")

    print("\n" + "=" * 60)
    print("MERGE SUMMARY")
    print("=" * 60)
    print(f"Original discussions: {original_count}")
    print(f"Merged discussions: {merged_count}")
    print(f"Reduction: {original_count - merged_count} discussions merged")
    print(f"Total tokens used: {metadata.tokens_used}")
    print(f"Total time: {metadata.latency_seconds:.2f}s")
    print("\n" + "=" * 60)
    print("\nMerged discussions:")
    for idx, discussion in enumerate(merged_result.discussions, 1):
        print(f"\n{idx}. {discussion.topic}")
        print(f"   Keywords: {', '.join(discussion.keywords[:5])}...")
        print(f"   Participants: {len(discussion.participants)} people")
        print(f"   Links: {len(discussion.message_links)} messages")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
