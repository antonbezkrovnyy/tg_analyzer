"""Analyze raw message data to understand discussion structure."""

import json
from collections import defaultdict
from pathlib import Path

# Load data
data_path = Path(
    r"C:\Users\Мой компьютер\Desktop\python-tg\data\ru_python\2025-11-05.json"
)
with open(data_path, encoding="utf-8") as f:
    data = json.load(f)

messages = data["messages"]
senders = data["senders"]

print("Анализ чата за 2025-11-05")
print(f"Всего сообщений: {len(messages)}\n")

# Analyze first 50 messages
print("=" * 80)
print("ПЕРВЫЕ 50 СООБЩЕНИЙ (в обратном порядке - от новых к старым):")
print("=" * 80)

for i, msg in enumerate(messages[:50]):
    sender = senders.get(str(msg["sender_id"]), "Unknown")
    text = (msg.get("text") or "")[:100].replace("\n", " ")
    reply = f"reply {msg['reply_to_msg_id']}" if msg.get("reply_to_msg_id") else "new"

    print(f"\n{i+1}. [{msg['id']}] {sender}")
    print(f"   {reply}")
    print(f"   {text}...")

# Find discussion threads
print("\n\n" + "=" * 80)
print("АНАЛИЗ ЦЕПОЧЕК ОБСУЖДЕНИЙ:")
print("=" * 80)

# Build reply chains
reply_chains = defaultdict(list)
for msg in messages[:50]:
    if msg.get("reply_to_msg_id"):
        reply_chains[msg["reply_to_msg_id"]].append(msg["id"])

# Find root messages (with most replies)
root_messages = [(msg_id, len(replies)) for msg_id, replies in reply_chains.items()]
root_messages.sort(key=lambda x: x[1], reverse=True)

print(f"\nТоп сообщений с ответами (первые 50):")
for msg_id, reply_count in root_messages[:10]:
    msg = next((m for m in messages if m["id"] == msg_id), None)
    if msg:
        sender = senders.get(str(msg["sender_id"]), "Unknown")
        text = (msg.get("text") or "")[:80].replace("\n", " ")
        print(f"\n[{msg_id}] {sender} ({reply_count} ответов)")
        print(f"   {text}...")

        # Show replies
        replies = reply_chains[msg_id]
        for reply_id in replies[:5]:
            reply_msg = next((m for m in messages if m["id"] == reply_id), None)
            if reply_msg:
                reply_sender = senders.get(str(reply_msg["sender_id"]), "Unknown")
                reply_text = (reply_msg.get("text") or "")[:60].replace("\n", " ")
                print(f"      > [{reply_id}] {reply_sender}: {reply_text}...")

# Analyze topics
print("\n\n" + "=" * 80)
print("ТЕМЫ ОБСУЖДЕНИЙ (по ключевым словам):")
print("=" * 80)

keywords: dict[str, list[int]] = {
    "gettext": [],
    "локализация": [],
    "ngettext": [],
    "i18n": [],
    "async": [],
    "asyncio": [],
    "database": [],
    "БД": [],
    "SQL": [],
    "Django": [],
    "FastAPI": [],
    "pytest": [],
    "тест": [],
}

for msg in messages[:100]:
    if not msg.get("text"):
        continue
    text_lower = msg["text"].lower()
    for keyword, msg_list in keywords.items():
        if keyword.lower() in text_lower:
            msg_list.append(msg["id"])

print("\nКлючевые слова в первых 100 сообщениях:")
for keyword, msg_ids in keywords.items():
    if msg_ids:
        print(f"  {keyword}: {len(msg_ids)} сообщений - {msg_ids[:5]}")

print("\n\n" + "=" * 80)
print("ВЫВОДЫ:")
print("=" * 80)
print(
    """
На основе анализа данных можно увидеть:
1. Сколько реальных технических дискуссий
2. Какие темы обсуждаются
3. Насколько они ценные
4. Сколько участников вовлечено
"""
)
