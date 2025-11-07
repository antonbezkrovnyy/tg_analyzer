# Data Structure from tg_fetcher

## Source Types

### 1. Channels (type="channel")
- **Особенность**: Есть `comments` - комментарии под постами
- **Структура обсуждения**: Пост → Комментарии (thread)
- **Пример**: Новостные каналы, блоги

```json
{
  "id": 123,
  "text": "Main post content",
  "comments": [
    {
      "id": 456,
      "text": "Comment under post",
      "sender_id": 789
    }
  ]
}
```

### 2. Chats/Supergroups (type="chat" or "supergroup")
- **Особенность**: `comments` всегда пустой массив `[]`
- **Структура обсуждения**: Сообщения + ответы через `reply_to_msg_id`
- **Пример**: Группы, супергруппы (@ru_python, @pythonstepikchat)

```json
{
  "id": 123,
  "text": "Question about Python",
  "reply_to_msg_id": null,
  "comments": []
},
{
  "id": 124,
  "text": "Answer to question",
  "reply_to_msg_id": 123,
  "comments": []
}
```

## Message Model

### Fields
- `id`: Message ID
- `date`: Timestamp
- `text`: Message text (optional)
- `sender_id`: Sender user ID
- `reply_to_msg_id`: ID of message this replies to (for chats)
- `forward_from`: Forward source (optional)
- `reactions`: List of reactions `[{emoji, count, users}]`
- `comments`: List of comments (only for channels, empty for chats)

### Helper Methods
```python
message.is_reply()  # Check if message replies to another
message.has_comments()  # Check if message has comments (channel feature)
```

## SourceInfo Model

### Fields
- `id`: Source ID
- `title`: Source title
- `url`: Source URL
- `type`: Source type ("channel", "chat", "supergroup")

### Helper Methods
```python
source_info.is_channel()  # True for channels (has comments)
source_info.is_chat()     # True for chats/supergroups (no comments)
```

## Processing Strategy

### For Chats (ru_python, pythonstepikchat)
1. ✅ Use message text
2. ✅ Track reply chains via `reply_to_msg_id`
3. ❌ Ignore `comments` field (always empty)
4. ✅ Use reactions to identify popular messages

### For Channels
1. ✅ Use post text
2. ✅ Process comments under posts
3. ✅ Track comment threads
4. ✅ Use reactions on both posts and comments

## Data Source

Messages loaded from `tg_fetcher` project:
- Path: `../python-tg/data/{chat_name}/{date}.json`
- Format: MessageDump JSON with version, source_info, senders, messages

## Current Implementation

### test_real_analysis.py
- ✅ Loads messages from tg_fetcher dumps
- ✅ Formats messages (ignores empty comments for chats)
- ✅ Sends to GigaChat for analysis
- 🔄 Handles both chats and channels transparently

### Future Enhancements
- Display reply chains in formatted output
- Show comment threads for channels
- Filter by reaction count
- Group messages by discussion threads
