# TZ: Базовая инфраструктура анализатора

## Статус
- [x] Создано
- [ ] В работе
- [ ] Реализовано

## Бизнес-цель
Создать базовую архитектуру для анализа Telegram-чатов с помощью GigaChat API. Цель - перейти от тестового скрипта к production-ready сервису с четкой структурой, переиспользуемыми компонентами и сохранением результатов.

## Текущее состояние
✅ **Работает**:
- Загрузка сообщений из JSON (MessageRepository)
- GigaChat OAuth + API клиент (GigaChatClient)
- Форматирование сообщений в JSON для GigaChat
- Промпт из файла `config/prompts/analysis_prompt.txt`
- Парсинг ответа GigaChat в модели Pydantic (Discussion, AnalysisResult)
- Валидация ссылок по формату `https://t.me/{chat_username}/{message_id}`

❌ **Проблемы**:
- Весь код в одном тестовом скрипте `scripts/test_real_analysis.py`
- Нет сохранения результатов в структурированном виде
- Нет переиспользуемых сервисов
- Промпт строится вручную каждый раз
- Нет CLI для запуска анализа

## Требования

### 1. AnalysisRepository - сохранение результатов

**Цель**: Сохранять результаты анализа в структурированном виде для последующего использования

**Функциональность**:
- Сохранение в `output/{chat}/{date}.json`
- Формат файла:
```json
{
  "metadata": {
    "chat": "ru_python",
    "chat_username": "ru_python",
    "date": "2025-11-05",
    "analyzed_at": "2025-11-07T12:29:08Z",
    "total_messages": 570,
    "analyzed_messages": 30,
    "tokens_used": 4014,
    "model": "GigaChat:2.0.28.2",
    "latency_seconds": 2.98
  },
  "discussions": [
    {
      "topic": "...",
      "keywords": ["...", "..."],
      "participants": ["...", "..."],
      "summary": "...",
      "expert_comment": "...",
      "message_links": ["https://t.me/ru_python/123", "..."]
    }
  ]
}
```

**API**:
```python
class AnalysisRepository:
    def __init__(self, output_dir: Path = Path("output")):
        self.output_dir = output_dir

    def save(
        self,
        chat: str,
        date: str,
        result: AnalysisResult,
        metadata: AnalysisMetadata
    ) -> Path:
        """Save analysis result to output/{chat}/{date}.json"""

    def load(self, chat: str, date: str) -> tuple[AnalysisResult, AnalysisMetadata]:
        """Load existing analysis from file"""

    def exists(self, chat: str, date: str) -> bool:
        """Check if analysis already exists"""

    def list_dates(self, chat: str) -> list[str]:
        """List all analyzed dates for chat"""
```

**Модели**:
```python
class AnalysisMetadata(BaseModel):
    chat: str
    chat_username: str
    date: str
    analyzed_at: datetime
    total_messages: int
    analyzed_messages: int
    tokens_used: int
    model: str
    latency_seconds: float
```

### 2. PromptBuilder - построение промптов

**Цель**: Формализовать процесс построения промптов, чтобы легко менять параметры

**Функциональность**:
- Загрузка шаблона из `config/prompts/analysis_prompt.txt`
- Форматирование сообщений (JSON или текст)
- Подстановка переменных (chat_name, chat_username, date, etc.)
- Поддержка разных стратегий форматирования

**API**:
```python
class PromptBuilder:
    def __init__(self, template_path: Path = Path("config/prompts/analysis_prompt.txt")):
        self.template_path = template_path
        self.template = self._load_template()

    def build(
        self,
        chat_name: str,
        chat_username: str,
        date: str,
        messages: list[Message],
        window_size: int = 30,
        format_style: Literal["json", "text"] = "json"
    ) -> str:
        """Build complete prompt for GigaChat"""

    def format_messages(
        self,
        messages: list[Message],
        style: Literal["json", "text"] = "json"
    ) -> str:
        """Format messages for prompt"""

    def _load_template(self) -> str:
        """Load prompt template from file"""
```

### 3. AnalyzerService - оркестрация pipeline

**Цель**: Объединить все компоненты в единый pipeline анализа

**Функциональность**:
- Загрузка сообщений (MessageRepository)
- Построение промпта (PromptBuilder)
- Отправка в GigaChat (GigaChatClient)
- Парсинг результата
- Валидация ссылок (опционально)
- Сохранение результата (AnalysisRepository)

**API**:
```python
class AnalyzerService:
    def __init__(
        self,
        message_repo: MessageRepository,
        gigachat_client: GigaChatClient,
        prompt_builder: PromptBuilder,
        analysis_repo: AnalysisRepository,
        validate_links: bool = True
    ):
        self.message_repo = message_repo
        self.gigachat_client = gigachat_client
        self.prompt_builder = prompt_builder
        self.analysis_repo = analysis_repo
        self.validate_links = validate_links

    async def analyze(
        self,
        chat: str,
        date: str,
        window_size: int = 30,
        force: bool = False
    ) -> AnalysisResult:
        """
        Analyze chat for specific date.

        Args:
            chat: Chat name (e.g., "ru_python")
            date: Date in YYYY-MM-DD format
            window_size: Number of messages to analyze
            force: Overwrite existing analysis

        Returns:
            AnalysisResult with discussions
        """

    def _validate_links(
        self,
        discussions: list[Discussion],
        chat_username: str,
        message_ids: list[int]
    ) -> list[str]:
        """Validate message_links in discussions. Returns list of errors."""
```

**Workflow**:
```
1. Check if analysis exists (if not force)
2. Load messages from MessageRepository
3. Build prompt with PromptBuilder
4. Send to GigaChat
5. Parse response to AnalysisResult
6. Validate links (if enabled)
7. Save to AnalysisRepository
8. Return result
```

### 4. LinkValidator - валидация ссылок (опционально)

**Цель**: Убедиться, что GigaChat сгенерировал корректные ссылки

**Функциональность**:
- Проверка формата `https://t.me/{chat_username}/{message_id}`
- Проверка, что username совпадает
- Проверка, что message_id существует в исходных данных
- Возврат списка ошибок/предупреждений

**API**:
```python
class LinkValidator:
    def validate_discussion(
        self,
        discussion: Discussion,
        chat_username: str,
        message_ids: list[int]
    ) -> ValidationResult:
        """Validate all links in discussion"""

class ValidationResult(BaseModel):
    is_valid: bool
    errors: list[str]
    warnings: list[str]
```

## Структура проекта

```
src/
├── repositories/
│   ├── message_repository.py       # ✅ Уже есть
│   └── analysis_repository.py      # NEW
├── services/
│   ├── gigachat_client.py          # ✅ Уже есть
│   ├── prompt_builder.py           # NEW
│   ├── analyzer_service.py         # NEW
│   └── link_validator.py           # NEW (опционально)
├── models/
│   ├── message.py                  # ✅ Уже есть
│   └── analysis.py                 # ✅ Уже есть (добавить AnalysisMetadata)
└── cli/
    └── analyze.py                  # NEW - CLI для запуска анализа

output/
├── ru_python/
│   ├── 2025-11-05.json
│   ├── 2025-11-06.json
│   └── ...
└── pythonstepikchat/
    ├── 2025-11-05.json
    └── ...
```

## План реализации

### Шаг 1: AnalysisRepository
1. Создать `src/repositories/analysis_repository.py`
2. Добавить `AnalysisMetadata` в `src/models/analysis.py`
3. Реализовать методы save, load, exists, list_dates
4. Написать unit тесты

### Шаг 2: PromptBuilder
1. Создать `src/services/prompt_builder.py`
2. Перенести логику из `test_real_analysis.py`
3. Добавить поддержку разных форматов (json/text)
4. Написать unit тесты

### Шаг 3: AnalyzerService
1. Создать `src/services/analyzer_service.py`
2. Объединить все компоненты
3. Реализовать полный pipeline
4. Добавить логирование
5. Написать integration тесты

### Шаг 4: LinkValidator (опционально)
1. Создать `src/services/link_validator.py`
2. Реализовать проверки
3. Интегрировать в AnalyzerService
4. Написать unit тесты

### Шаг 5: CLI
1. Создать `src/cli/analyze.py`
2. Добавить команды:
   - `analyze <chat> <date>` - анализ одной даты
   - `analyze <chat> --from <date> --to <date>` - диапазон дат
   - `analyze <chat> --all` - все доступные даты
3. Добавить флаги: `--force`, `--window-size`, `--no-validation`

## Acceptance Criteria

✅ **AnalysisRepository**:
- Сохраняет результаты в `output/{chat}/{date}.json`
- Загружает существующие результаты
- Создает директории автоматически
- Список всех дат для чата

✅ **PromptBuilder**:
- Загружает шаблон из файла
- Подставляет все переменные
- Форматирует сообщения в JSON
- Возвращает готовый промпт

✅ **AnalyzerService**:
- Полный pipeline от загрузки до сохранения
- Не перезаписывает существующие анализы (если не force)
- Логирует все шаги
- Возвращает результат

✅ **LinkValidator**:
- Проверяет формат ссылок
- Проверяет username
- Проверяет существование message_id
- Возвращает понятные ошибки

## Зависимости
- MessageRepository ✅
- GigaChatClient ✅
- Pydantic модели (Message, Discussion, AnalysisResult) ✅
- Prompt template в `config/prompts/analysis_prompt.txt` ✅

## Риски
- **Производительность**: При анализе многих дат может быть долго (решение: async/await)
- **Токены**: Большие окна сообщений могут превысить лимит (решение: chunking в будущем)
- **Ошибки GigaChat**: Иногда может не распарсить JSON (решение: retry + fallback)

## Приоритет
**Высокий** - это базовая инфраструктура для всех дальнейших улучшений
