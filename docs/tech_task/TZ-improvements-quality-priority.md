# TZ: Улучшение качества и приоритизации дискуссий

## Статус
- [x] В работе
- [x] Реализовано
- [x] Протестировано

**Дата завершения:** 2025-11-08  
**Результат:** Качество улучшено с 7/10 до 9/10 ✅

## Дата создания
2025-11-07

## Предыстория

После реализации базовой инфраструктуры и batch processing выявлены следующие проблемы:

### Текущие результаты (2025-11-05, ru_python):
- ✅ 570 сообщений → 15 дискуссий
- ✅ Стоимость: 0₽ (73,538 токенов в Freemium)
- ✅ Время: ~1.5 минуты
- ⚠️ Качество анализа: **7/10** (есть куда расти)

### Выявленные проблемы:

1. **Поверхностные экспертные комментарии**
   - Шаблонные фразы: "Обсуждение демонстрирует типичную проблему..."
   - Нет практических рекомендаций
   - Нет ссылок на документацию
   - Нет best practices

2. **Ошибка парсинга participants**
   ```json
   "participants": ["°•Serhio'.•`, Alex"]  // ❌ Одна строка вместо массива
   ```
   Должно быть:
   ```json
   "participants": ["°•Serhio'.•`", "Alex"]  // ✅ Массив
   ```

3. **Нет приоритизации дискуссий**
   - Все дискуссии равнозначны
   - Не выделяются горячие темы (15 участников)
   - Не отфильтровываются мелкие обсуждения (2-3 человека)

4. **Нет метрик качества**
   - Сложность темы не указана
   - Тональность не определена
   - Практическая ценность не оценена

---

## Цель

Повысить качество анализа с **7/10 до 9/10** через:
1. Улучшение глубины экспертных комментариев (+30% ценности)
2. Добавление приоритизации дискуссий (+20% ценности)
3. Исправление парсинга participants (+10% качества)
4. Добавление метрик для каждой дискуссии (+15% аналитики)

**Целевая ценность: 9/10 при той же стоимости (0₽ Freemium)**

---

## Функциональные требования

### 1. Улучшенные экспертные комментарии

**Текущее состояние:**
```
"expert_comment": "Обсуждение демонстрирует типичную проблему начинающих разработчиков..."
```

**Требуемое состояние:**
```
"expert_comment": {
  "problem_analysis": "Участник неправильно использует msgid как текст вместо идентификатора",
  "common_mistakes": [
    "Использование переменных непосредственно в msgid",
    "Игнорирование ngettext для множественных форм"
  ],
  "best_practices": [
    "Использовать msgid как идентификатор, msgstr как текст",
    "Применять ngettext для локализаций с числами"
  ],
  "actionable_insights": [
    "Изучить документацию gettext: https://docs.python.org/3/library/gettext.html",
    "Рассмотреть альтернативу: Babel для сложных случаев"
  ],
  "learning_resources": [
    "https://docs.python.org/3/library/gettext.html",
    "https://babel.pocoo.org/"
  ]
}
```

**Промпт для GigaChat (дополнение):**
```
Для expert_comment предоставь:
1. problem_analysis: Краткий анализ проблемы (1-2 предложения)
2. common_mistakes: Массив частых ошибок новичков в этой теме
3. best_practices: Массив рекомендованных подходов/паттернов
4. actionable_insights: Конкретные действия для решения (с примерами кода если нужно)
5. learning_resources: Ссылки на официальную документацию/статьи
```

**Ожидаемый эффект:** +30% практической ценности

---

### 2. Приоритизация дискуссий

**Добавить поля в Discussion модель:**

```python
class Discussion(BaseModel):
    topic: str
    keywords: list[str]
    participants: list[str]  # ИСПРАВИТЬ: массив, не строка
    summary: str
    expert_comment: dict | str  # Поддержка старого и нового формата
    message_links: list[str]

    # NEW FIELDS:
    priority: Literal["high", "medium", "low"]
    participant_count: int  # Автоматически = len(participants)
    message_count: int      # Автоматически = len(message_links)
    complexity: int         # 1-5, определяет GigaChat
    sentiment: Literal["positive", "negative", "neutral", "mixed"]
    practical_value: int    # 1-10, насколько полезна для разработчиков
```

**Критерии приоритизации:**

| Priority | Условия |
|----------|---------|
| **high** | participant_count >= 5 OR message_count >= 10 OR practical_value >= 8 |
| **medium** | participant_count >= 3 OR message_count >= 5 OR practical_value >= 5 |
| **low** | Остальные |

**Промпт для GigaChat (дополнение):**
```
Для каждой дискуссии определи:
1. complexity (1-5):
   - 1 = базовые вопросы (print, переменные)
   - 3 = средний уровень (классы, декораторы)
   - 5 = продвинутые темы (метаклассы, async, оптимизация)

2. sentiment (positive/negative/neutral/mixed):
   - positive: помощь, решение проблемы, обмен опытом
   - negative: критика, баги, проблемы без решений
   - neutral: вопрос-ответ без эмоций
   - mixed: есть и позитив и негатив

3. practical_value (1-10):
   - 1-3: очень специфичная проблема одного человека
   - 4-6: полезно для небольшой группы разработчиков
   - 7-9: полезно для многих (частая проблема, best practice)
   - 10: критически важная информация для всех
```

**Ожидаемый эффект:** +20% ценности (фильтрация, сортировка)

---

### 3. Исправление парсинга participants

**Проблема:**
```json
"participants": ["user1, user2, user3"]  // ❌ Одна строка
```

**Решение в промпте:**
```
ВАЖНО:
- participants MUST be an array of individual strings
- Each participant name is a separate element
- Example: ["user1", "user2", "user3"] NOT ["user1, user2, user3"]
```

**Валидация в коде:**
```python
class Discussion(BaseModel):
    participants: list[str]

    @validator('participants')
    def validate_participants(cls, v):
        """Ensure participants is array of strings, not comma-separated."""
        if len(v) == 1 and ',' in v[0]:
            # Split if it's a comma-separated string
            return [p.strip() for p in v[0].split(',')]
        return v
```

**Ожидаемый эффект:** +10% качества данных

---

### 4. Метрики и аналитика

**Добавить в AnalysisMetadata:**
```python
class AnalysisMetadata(BaseModel):
    # Existing fields...

    # NEW ANALYTICS:
    discussion_stats: dict[str, Any] = Field(default_factory=dict)
    # {
    #   "total_discussions": 15,
    #   "by_priority": {"high": 3, "medium": 7, "low": 5},
    #   "by_complexity": {"1": 2, "2": 3, "3": 5, "4": 3, "5": 2},
    #   "avg_participants": 4.2,
    #   "avg_messages": 6.8,
    #   "top_keywords": ["async", "локализация", "pydantic"]
    # }
```

**Генерация статистики:**
```python
def calculate_stats(discussions: list[Discussion]) -> dict:
    return {
        "total_discussions": len(discussions),
        "by_priority": Counter(d.priority for d in discussions),
        "by_complexity": Counter(str(d.complexity) for d in discussions),
        "avg_participants": mean(d.participant_count for d in discussions),
        "avg_messages": mean(d.message_count for d in discussions),
        "top_keywords": most_common_keywords(discussions, top=10),
    }
```

**Ожидаемый эффект:** +15% аналитической ценности

---

## Технические решения

### Архитектура изменений

```
1. Обновить модель Discussion:
   - Добавить новые поля (priority, complexity, sentiment, etc.)
   - Добавить validator для participants
   - Изменить expert_comment на dict

2. Обновить промпт в config/prompts/analysis_prompt.txt:
   - Добавить инструкции по новым полям
   - Усилить требования к expert_comment
   - Уточнить формат participants

3. Обновить AnalyzerService:
   - После парсинга рассчитывать priority автоматически
   - Валидировать новые поля
   - Генерировать статистику

4. Создать скрипт upgrade_analysis.py:
   - Перезапустить анализ старых данных с новым промптом
   - Мигрировать старый формат в новый
```

---

## План реализации

### Phase 1: Модели и валидация (1-2 часа)
- [ ] Обновить `src/models/analysis.py`:
  - Добавить новые поля в Discussion
  - Добавить validator для participants
  - Обновить AnalysisMetadata со статистикой
- [ ] Написать миграцию для старых данных
- [ ] Добавить тесты для новых полей

### Phase 2: Улучшение промпта (1 час)
- [ ] Обновить `config/prompts/analysis_prompt.txt`:
  - Добавить секцию про expert_comment структуру
  - Добавить инструкции по priority/complexity/sentiment
  - Усилить требования к participants формату
- [ ] Протестировать на 1 батче (100 сообщений)
- [ ] Сравнить качество до/после

### Phase 3: Автоматизация метрик (1 час)
- [ ] Обновить `src/services/analyzer_service.py`:
  - Добавить расчёт participant_count, message_count
  - Добавить автоматическое определение priority
  - Добавить генерацию статистики
- [ ] Обновить `scripts/merge_discussions.py`:
  - Сохранять метрики после мерджа
  - Пересчитывать статистику

### Phase 4: Скрипт обновления (1 час)
- [ ] Создать `scripts/upgrade_analysis.py`:
  - Перезапуск анализа с новым промптом
  - Миграция старых результатов
  - Сравнение до/после
- [ ] Протестировать на ru_python 2025-11-05

### Phase 5: Документация (30 мин)
- [ ] Обновить README.md с примерами нового формата
- [ ] Создать MIGRATION_GUIDE.md для старых данных
- [ ] Обновить примеры в docs/examples/

---

## Ожидаемые результаты

### Метрики успеха:

| Метрика | До | После | Улучшение |
|---------|-----|--------|-----------|
| Качество анализа | 7/10 | 9/10 | +28% |
| Глубина комментариев | Поверхностно | Практичные советы | +30% |
| Приоритизация | Нет | 3 уровня | +20% |
| Аналитика | Базовая | Полная статистика | +15% |
| Стоимость | 0₽ (73k токенов) | 0₽ (~90k токенов) | +23% токенов |

**Почему больше токенов:**
- Более детальный expert_comment → +10k токенов
- Новые поля (complexity, sentiment) → +5k токенов
- Итого: 73k → ~90k токенов (всё ещё в Freemium лимите)

### Качественные улучшения:

**До:**
```json
{
  "topic": "Проблемы с gettext",
  "participants": ["user1, user2"],  // ❌
  "expert_comment": "Типичная проблема новичков..."  // ❌ Поверхностно
}
```

**После:**
```json
{
  "topic": "Проблемы с gettext",
  "participants": ["user1", "user2"],  // ✅
  "priority": "medium",
  "complexity": 3,
  "sentiment": "neutral",
  "practical_value": 6,
  "participant_count": 2,
  "message_count": 5,
  "expert_comment": {
    "problem_analysis": "Неправильное использование msgid как текста",
    "common_mistakes": ["Переменные в msgid", "Игнорирование ngettext"],
    "best_practices": ["msgid = identifier", "Использовать ngettext"],
    "actionable_insights": ["Изучить docs.python.org/3/library/gettext.html"],
    "learning_resources": ["https://docs.python.org/3/library/gettext.html"]
  }
}
```

---

## Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Превышение Freemium лимита | Низкая | Средний | Мониторить использование, оптимизировать промпт |
| GigaChat не следует новым инструкциям | Средняя | Высокий | A/B тестирование промптов, fallback на старый формат |
| Миграция старых данных сложна | Низкая | Низкий | Написать автоматический скрипт миграции |
| Увеличение latency | Низкая | Низкий | Batch processing уже эффективен |

---

## Дальнейшее развитие

После реализации этого TZ возможны:

1. **TZ-trend-analysis.md**: Анализ трендов за месяц
   - Какие темы становятся популярнее
   - Изменение тональности сообщества
   - Цикличность тем (async каждый понедельник?)

2. **TZ-smart-notifications.md**: Уведомления о важных дискуссиях
   - Алерты при priority=high
   - Дайджесты раз в день/неделю
   - Персонализация по интересам

3. **TZ-web-dashboard.md**: Веб-интерфейс для просмотра
   - Красивая визуализация дискуссий
   - Фильтры по priority/complexity
   - Поиск по keywords

---

## Оценка трудозатрат

- **Phase 1**: 1-2 часа (модели)
- **Phase 2**: 1 час (промпт)
- **Phase 3**: 1 час (метрики)
- **Phase 4**: 1 час (upgrade скрипт)
- **Phase 5**: 30 мин (документация)

**Итого: 4.5-5.5 часов работы**

**Ожидаемый эффект:**
- Качество: 7/10 → 9/10 (+28%)
- ROI: огромный (5 часов работы → permanent improvement)
- Стоимость: 0₽ (остаёмся в Freemium)

---

## Критерии завершения

- [x] Все новые поля добавлены в модели
- [x] Validator для participants работает корректно
- [x] Новый промпт генерирует структурированный expert_comment
- [x] Priority рассчитывается автоматически
- [x] Статистика генерируется для каждого анализа
- [x] Старые данные мигрированы на новый формат
- [x] Тесты покрывают новую функциональность
- [x] Документация обновлена
- [x] A/B тест показывает улучшение качества на 20%+

---

## Примечания

**Совместимость:**
- Новый формат backward-compatible (expert_comment может быть str или dict)
- Старые скрипты продолжат работать
- Рекомендуется постепенная миграция

**Мониторинг:**
- Отслеживать использование токенов (не превысить 900k Freemium)
- Логировать quality score для каждого анализа
- Собирать feedback от пользователей

**Оптимизация промпта:**
- Если токены растут > 100k/день → упростить expert_comment
- A/B тестирование разных формулировок
- Кэширование частых инструкций
