# Руководство по работе с анализатором (tg_analyzer)

Это практическая инструкция по запуску анализатора, отправке заданий через Redis и проверке результата. Подходит для локальной разработки и интеграции с остальными сервисами экосистемы (python-tg, tg_web).

## Введение и назначение

Анализатор принимает события о готовых выгрузках сообщений (из Telegram fetcher), порционно (батчами) обрабатывает сообщения с помощью LLM (GigaChat), объединяет темы дискуссий и сохраняет результат в JSON на хосте.

Ключевые возможности:
- Подписка на события из Redis и автоматический запуск анализа.
- Батч-обработка (по 100 сообщений) с слиянием тем и валидацией ссылок на сообщения.
- Сохранение результата в `tg_analyzer/output/<chat>/<date>.json`.

## Архитектура потока (fetcher → Redis → analyzer → output)

1. Fetcher (сервис из репозитория `python-tg`) выгружает сообщения и записывает файл в `python-tg/data/<chat>/<date>.json`.
2. Fetcher публикует событие в Redis (`tg_events.messages_fetched`).
3. Анализатор (`tg_analyzer`) слушает канал событий, получает уведомление и запускает анализ указанного чата/даты.
4. Результат анализа сохраняется в `tg_analyzer/output/<chat>/<date>.json` на хостовой машине.

## Быстрый старт

### Запуск инфраструктуры

Запустите общий стек инфраструктуры (Redis, Grafana, Prometheus, Loki):

```powershell
# из папки infrastructure
docker compose -f .\docker-compose.yml up -d
```

Проверьте, что Redis поднялся и доступен как контейнер `tg-redis`.

### Запуск fetcher и analyzer

Fetcher (демон, слушает очередь команд в Redis):

```powershell
# из папки python-tg
docker compose -f .\docker-compose.yml up -d telegram-fetcher
```

Analyzer (демон, слушает события и запускает анализ):

```powershell
# из папки tg_analyzer
docker compose -f .\docker-compose.yml up -d tg_analyzer
```

Проверка логов:

```powershell
# последние сообщения логов
docker logs --since 30s telegram-fetcher
docker logs --since 30s tg_analyzer
```

## Отправка задач (через Redis)

Обычно запуск анализа происходит автоматически после успешного fetch. Но можно инициировать полный путь явно: сначала отправить команду fetch, затем дождаться события и анализа.

### Формат JSON команды

```json
{
  "command": "fetch",
  "chat": "ru_python",     // без @
  "date": "2025-11-09",    // формат YYYY-MM-DD
  "requested_by": "copilot",
  "timestamp": "2025-11-10T11:05:00Z"
}
```

### Способы отправки (stdin, файл, redis-cli)

Рекомендуемый способ под Windows PowerShell: скопировать файл в контейнер Redis и запушить через stdin, чтобы избежать проблем с кавычками.

```powershell
# 1) подготовьте файл команды
Set-Content -LiteralPath .\cmd_fetch.json -Value '{"command":"fetch","chat":"ru_python","date":"2025-11-09","requested_by":"copilot","timestamp":"2025-11-10T11:05:00Z"}'

# 2) скопируйте файл в контейнер Redis
docker cp .\cmd_fetch.json tg-redis:/tmp/cmd.json

# 3) запишите команду в очередь tg_commands
docker exec tg-redis sh -lc "cat /tmp/cmd.json | redis-cli -x RPUSH tg_commands"
```

Альтернативно (через stdin без файла, безопасно в PowerShell):

```powershell
# обратите внимание на экранирование обратными кавычками в PowerShell
docker exec tg-redis sh -lc "printf '%s' '{`"command`":`"fetch`",`"chat`":`"ru_python`",`"date`":`"2025-11-09`",`"requested_by`":`"copilot`",`"timestamp`":`"2025-11-10T11:05:00Z`"}' | redis-cli -x RPUSH tg_commands"
```

Проверка принятия команды fetcher’ом:

```powershell
docker logs --since 60s telegram-fetcher
```

В логе ожидаем строки вида `Received command from queue` и завершение `Fetch completed successfully`.

## Ручной анализ (one-off run)

Для диагностик можно запустить анализ напрямую внутри контейнера анализатора:

```powershell
# Пример: анализ конкретного чата/даты вручную (упрощённая форма)
docker exec tg_analyzer sh -lc "python - <<'PY'
import asyncio
from pathlib import Path
from src.repositories.message_repository import MessageRepository
from src.repositories.analysis_repository import AnalysisRepository
from src.services.gigachat_client import GigaChatClient
from src.services.prompt_builder import PromptBuilder
from src.services.analyzer_service import AnalyzerService

async def run():
    msg_repo = MessageRepository(data_path=Path('/data'))
    analysis_repo = AnalysisRepository(output_dir=Path('/output'))
    client = GigaChatClient()
    builder = PromptBuilder()
    service = AnalyzerService(msg_repo, client, builder, analysis_repo)
    # force=True перезапишет существующий файл результата
    res, meta = await service.analyze(chat='ru_python', date='2025-11-09', force=True)
    print('Done', meta.analyzed_messages, 'of', meta.total_messages)

asyncio.run(run())
PY"
```

## Параметры и конфигурация (.env, переменные среды)

Ключевые переменные для `tg_analyzer` (см. `docker-compose.yml` в проекте анализатора):

- `GIGACHAT_AUTH_KEY` — ключ доступа к GigaChat (обязателен)
- `GIGACHAT_OAUTH_URL`, `GIGACHAT_BASE_URL`, `GIGACHAT_SCOPE`, `GIGACHAT_MODEL` — параметры GigaChat
- `TG_FETCHER_DATA_PATH` — путь к данным fetcher внутри контейнера (по умолчанию `/data`)
- `OUTPUT_PATH` — путь сохранения результата внутри контейнера (по умолчанию `/output`)
- `REDIS_URL`, `REDIS_PASSWORD` — подключение к Redis
- `WINDOW_SIZE` — исторический параметр окна (реальный анализ идёт батчами, см. ниже)
- `WORKER_ID` — ID воркера для логов и масштабирования

Для `python-tg` (fetcher):
- `REDIS_URL`, `REDIS_PASSWORD` — для команд/событий
- Параметры сессий Telethon и список чатов в конфигурации fetcher

## Batch-анализ и объединение

Анализатор обрабатывает сообщения порциями (по умолчанию `batch_size=100`), чтобы полно покрыть день. Для каждого батча формируется промпт, ответы объединяются:
- Схожие темы склеиваются по нормализованному названию (`topic`), объединяются `keywords`, `participants`, `message_links`.
- Ссылки валидируются — допускаются только ID, присутствующие во входных данных.
- Метаданные (`analyzed_messages`) считают все сообщения за день.

## Формат выходного JSON (metadata, discussions)

Минимальная структура:

```json
{
  "metadata": {
    "chat": "ru_python",
    "chat_username": "ru_python",
    "date": "2025-11-09",
    "analyzed_at": "2025-11-10 10:20:16.042706",
    "total_messages": 142,
    "analyzed_messages": 142,
    "tokens_used": 20233,
    "model": "GigaChat:2.0.28.2",
    "latency_seconds": 34.58,
    "discussion_stats": { "total_discussions": 6, "by_complexity": {"2":1,"3":3,"4":2} }
  },
  "discussions": [
    {
      "topic": "...",
      "keywords": ["..."],
      "participants": ["..."],
      "summary": "...",
      "expert_comment": {
        "problem_analysis": "...",
        "common_mistakes": ["..."],
        "best_practices": ["..."],
        "actionable_insights": ["..."],
        "learning_resources": ["https://..."]
      },
      "message_links": ["https://t.me/ru_python/2642335", "..."]
      ,"complexity": 3,
      "sentiment": "neutral",
      "practical_value": 8
    }
  ]
}
```

Примечание: LLM может добавить лишние поля — они не обязательны. При интеграции ориентируйтесь на обязательные поля, перечисленные выше.

## Перезапись и обновление результатов

- Автоматически: демон анализатора перезаписывает существующий файл за дату, если событие пришло повторно.
- Вручную: передайте `force=True` в ручном запуске (см. пример выше).
- Проверка: убедитесь, что время изменения файла на хосте обновилось.

## Troubleshooting (симптом → причина → решение)

| Симптом | Возможная причина | Что сделать |
|---|---|---|
| `JSONDecodeError` в логах fetcher при чтении команды | Некорректные кавычки/экранирование JSON в PowerShell | Используйте способ с файлом и stdin через `redis-cli -x`, см. раздел «Отправка задач» |
| `KeyError` при форматировании промпта в analyzer | Неэкранированные фигурные скобки в шаблоне промпта | Убедитесь, что шаблон в `config/prompts/analysis_prompt.txt` экранирует `{}` как `{{ }}` |
| Файл результата не появляется/не обновляется | Том `/output` не смонтирован или путь неверный | Проверьте том в `tg_analyzer/docker-compose.yml` и права; смотрите логи `tg_analyzer` |
| Fetch завершился, но analyzer молчит | Нет события или нет подписки | Проверьте логи Redis PubSub и `tg_analyzer`; `docker logs --since 60s tg_analyzer` |
| Ошибка OAuth/токена GigaChat | Истёк ключ/неверные URL | Обновите `GIGACHAT_AUTH_KEY` и URL’ы, перезапустите контейнер |

## FAQ

- Можно ли анализировать несколько дат? — Да, отправляйте команды fetch по нужным датам последовательно.
- Можно ли ускорить? — Масштабируйте воркеры analyzer (разные `WORKER_ID`), следите за rate limits GigaChat.
- Почему не все темы попадают? — Промпт отбирает только связанные дискуссии с ≥2 содержательными сообщениями.

## Интеграция с веб-слоем (tg_web) — обзор

В текущей конфигурации веб-слой (`tg_web`) может читать готовые JSON из `tg_analyzer/output`. Дальше планируется автоматический импорт через события (например, `analysis.completed`) и фоновую задачу, которая пишет в БД веб-приложения. Пока используйте файловый обмен или настройте периодический импорт.

---

Готово. Если нужно — добавлю пост-валидацию для удаления лишних полей из `discussions` и авто-репромпт при нарушении схемы.
