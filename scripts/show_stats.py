"""Show analysis statistics for all dates."""

import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "ru_python"

dates = ["2025-11-05", "2025-11-06", "2025-11-07"]

print("=" * 70)
print("СТАТИСТИКА АНАЛИЗА")
print("=" * 70)

total_discs = 0
total_tokens = 0

for date in dates:
    file_path = OUTPUT_DIR / f"{date}.json"
    if not file_path.exists():
        print(f"\n{date}: файл не найден")
        continue

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    disc_count = len(data["discussions"])
    tokens = data["metadata"]["tokens_used"]
    total_discs += disc_count
    total_tokens += tokens

    print(f"\n📅 {date}:")
    print(f"  Дискуссий: {disc_count}")
    print(f"  Токенов: {tokens}")
    
    if "discussion_stats" in data["metadata"]:
        stats = data["metadata"]["discussion_stats"]
        print(f"  По приоритету: {stats.get('by_priority', {})}")
        print(f"  По сложности: {stats.get('by_complexity', {})}")
        print(f"  Средние участники: {stats.get('avg_participants', 0):.1f}")
        print(f"  Средние сообщения: {stats.get('avg_messages', 0):.1f}")

    print(f"\n  Детали:")
    for disc in data["discussions"]:
        topic = disc["topic"][:60]
        priority = disc.get("priority", "N/A")
        complexity = disc.get("complexity", "N/A")
        value = disc.get("practical_value", "N/A")
        participants = len(disc.get("participants", []))
        messages = disc.get("message_count", len(disc.get("message_links", [])))
        
        print(f"    • {topic}")
        print(f"      ├ Priority: {priority}, Complexity: {complexity}/5, Value: {value}/10")
        print(f"      └ {participants} участников, {messages} сообщений")

print(f"\n{'=' * 70}")
print(f"📊 ИТОГО: {total_discs} дискуссий, {total_tokens:,} токенов")
print(f"   Средний расход: {total_tokens // total_discs if total_discs > 0 else 0:,} токенов на дискуссию")
print("=" * 70)
