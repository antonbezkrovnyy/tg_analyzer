"""Create test data for merge_discussions.py testing."""

import json
from pathlib import Path

# Create a test file with duplicate discussions
test_data = {
    "metadata": {
        "chat": "ru_python",
        "chat_username": "ru_python",
        "date": "2025-11-TEST",
        "analyzed_at": "2025-11-08 00:00:00",
        "total_messages": 100,
        "analyzed_messages": 100,
        "tokens_used": 10000,
        "model": "GigaChat:2.0.28.2",
        "latency_seconds": 10.0,
        "discussion_stats": {
            "total_discussions": 3,
            "by_priority": {"high": 2, "medium": 1},
            "by_complexity": {"3": 3},
            "avg_participants": 5,
            "avg_messages": 10,
            "avg_complexity": 3,
            "avg_practical_value": 7,
            "top_keywords": ["Python", "синглтон", "глобалы"]
        }
    },
    "discussions": [
        {
            "topic": "Использование глобальных переменных в Python",
            "keywords": ["Python", "глобалы", "переменные"],
            "participants": ["Владимир", "lightmanLP", "Tishka17"],
            "summary": "Обсуждение глобальных переменных. Часть 1: введение в проблематику.",
            "expert_comment": {
                "problem_analysis": "Проблема использования глобальных переменных в Python.",
                "common_mistakes": [
                    "Злоупотребление глобальными переменными"
                ],
                "best_practices": [
                    "Использование классов вместо глобальных переменных"
                ],
                "actionable_insights": [
                    "Избегать глобальных переменных в сложных приложениях"
                ],
                "learning_resources": [
                    "https://docs.python.org/3/glossary.html#term-global"
                ]
            },
            "message_links": [
                "https://t.me/ru_python/2641549",
                "https://t.me/ru_python/2641548"
            ],
            "priority": "high",
            "participant_count": 3,
            "message_count": 2,
            "complexity": 3,
            "sentiment": "neutral",
            "practical_value": 7
        },
        {
            "topic": "Синглтон vs глобальные переменные",
            "keywords": ["Python", "синглтон", "глобалы"],
            "participants": ["Kan", "Jack Bolt", "r nurnu", "Никита Пастухов"],
            "summary": "Сравнение синглтонов и глобальных переменных. Часть 2: углубление в тему.",
            "expert_comment": {
                "problem_analysis": "Выбор между синглтоном и глобальными переменными.",
                "common_mistakes": [
                    "Переоценка преимуществ синглтонов"
                ],
                "best_practices": [
                    "Избегание ленивой инициализации в синглтонах"
                ],
                "actionable_insights": [
                    "Использовать замыкание для простых случаев"
                ],
                "learning_resources": [
                    "https://www.python.org/dev/peps/pep-0318/"
                ]
            },
            "message_links": [
                "https://t.me/ru_python/2641547",
                "https://t.me/ru_python/2641546",
                "https://t.me/ru_python/2641545"
            ],
            "priority": "high",
            "participant_count": 4,
            "message_count": 3,
            "complexity": 3,
            "sentiment": "neutral",
            "practical_value": 8
        },
        {
            "topic": "RabbitMQ: основы работы",
            "keywords": ["RabbitMQ", "очереди", "сообщения"],
            "participants": ["Алексей", "Мария"],
            "summary": "Базовое обсуждение RabbitMQ для начинающих.",
            "expert_comment": {
                "problem_analysis": "Понимание основ работы с RabbitMQ.",
                "common_mistakes": [
                    "Неправильная конфигурация очередей"
                ],
                "best_practices": [
                    "Использование подтверждений сообщений"
                ],
                "actionable_insights": [
                    "Настроить dead-letter exchange"
                ],
                "learning_resources": [
                    "https://www.rabbitmq.com/tutorials/tutorial-one-python.html"
                ]
            },
            "message_links": [
                "https://t.me/ru_python/2641544"
            ],
            "priority": "medium",
            "participant_count": 2,
            "message_count": 1,
            "complexity": 3,
            "sentiment": "positive",
            "practical_value": 6
        }
    ]
}

# Save to output directory
output_dir = Path(__file__).parent.parent / "output" / "ru_python"
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "2025-11-TEST.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(test_data, f, indent=2, ensure_ascii=False)

print(f"✓ Test data created: {output_file}")
print(f"  Discussions: {len(test_data['discussions'])}")
print("  Expected merge: Discussion 1 + Discussion 2 → 1 merged")
print("  Expected result: 2 discussions total")
