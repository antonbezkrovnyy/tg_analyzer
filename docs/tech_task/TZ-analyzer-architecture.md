# TZ: Telegram Chat Analyzer - Full Project Architecture

**Created:** November 7, 2025
**Status:** ⚙️ In Progress
**Version:** 1.0

---

## 📋 Business Goal

Create a Python service that analyzes Telegram chat messages (collected by `tg_fetcher`) using **Sber GigaChat API** to extract insights, summarize discussions, and provide structured analysis results.

**Primary Use Case:** Daily chat summarization with topic extraction, key participants, and expert commentary.

---

## ✅ Functional Requirements

### Core Features (MVP)
1. **Read JSON dumps from tg_fetcher**
   - Input format: `data/{chat_name}/{YYYY-MM-DD}.json`
   - Schema: see example `../python-tg/data/ru_python/2025-11-06.json`
   - One file = one chat = one day

2. **Analyze messages using GigaChat API**
   - Model: GigaChat Lite (configurable for future upgrade to Plus/Pro)
   - Authentication: API key via environment variables
   - Rate limiting: handle API limits gracefully (retry with backoff)

3. **Generate structured analysis**
   - Output format: JSON (similar to `answer_ru_python_2025-11-03.json`)
   - Required fields:
     - `discussions[]` - list of topics discussed
       - `topic` - topic name
       - `keywords[]` - key terms
       - `participants[]` - active users
       - `summary` - discussion summary
       - `expert_comment` - AI-generated expert perspective
       - `message_links[]` - relevant Telegram message URLs
   - Save prompt and response for audit/debugging

4. **Store results with history**
   - Output location: `output/{chat_name}/{YYYY-MM-DD}_analysis.json`
   - Keep history of all analyses (don't overwrite)
   - Store metadata: analysis timestamp, model used, token count

5. **Interface (Phase 1: CLI)**
   - Command: `analyze --chat ru_python --date 2025-11-06`
   - Parameters:
     - `--chat` (required) - chat name
     - `--date` (required) - date in YYYY-MM-DD format
     - `--output` (optional) - custom output path
     - `--model` (optional) - override default GigaChat model
   - Interactive mode: later phase (select chat from list, date picker)

6. **Observability Integration**
   - Log all GigaChat API calls (prompt, response, latency, tokens)
   - Metrics: API call count, success/failure rate, cost tracking
   - Use observability-stack (Loki, Prometheus, Grafana)

### Future Features (Post-MVP)
- API interface (FastAPI) for programmatic access
- Multi-day trend analysis
- Chat comparison
- Semantic search over analyzed content
- Export to PDF/HTML reports
- Real-time analysis (webhook from tg_fetcher)

---

## 🏗️ Technical Architecture

### Project Structure

```
tg_analyzer/
├── src/
│   ├── __init__.py
│   ├── main.py                    # CLI entry point
│   ├── cli/
│   │   ├── __init__.py
│   │   └── commands.py            # Click commands
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Pydantic Settings
│   │   └── exceptions.py          # Custom exceptions
│   ├── models/
│   │   ├── __init__.py
│   │   ├── message.py             # Reuse from tg_fetcher or define here
│   │   ├── analysis.py            # Analysis result schema
│   │   └── gigachat.py            # GigaChat API request/response models
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── message_repository.py  # Read JSON dumps
│   │   └── analysis_repository.py # Save analysis results
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gigachat_client.py     # GigaChat API wrapper
│   │   ├── analyzer_service.py    # Orchestrates analysis
│   │   └── prompt_builder.py      # Constructs prompts for GigaChat
│   └── utils/
│       ├── __init__.py
│       ├── logger.py              # Logging setup with Loki
│       └── metrics.py             # Prometheus metrics
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_message_repository.py
│   │   ├── test_gigachat_client.py
│   │   └── test_analyzer_service.py
│   ├── integration/
│   │   └── test_full_analysis.py
│   └── fixtures/
│       ├── sample_messages.json   # Test data
│       └── sample_analysis.json   # Expected output
├── docs/
│   ├── PRE_IMPLEMENTATION_CHECKLIST.md
│   ├── tech_task/
│   │   └── TZ-analyzer-architecture.md  # This file
│   └── console.log                # Command execution log
├── config/
│   ├── prompts/
│   │   └── summarization.txt      # Default prompt template
│   └── settings.yml               # Optional YAML config
├── output/                        # Analysis results (gitignored)
│   └── ru_python/
│       └── 2025-11-06_analysis.json
├── scripts/
│   └── quickstart.ps1             # Quick setup script
├── .env.example                   # Environment variables template
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml                 # Project metadata (black, isort, mypy config)
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Dev dependencies (pytest, black, etc.)
└── README.md
```

### Data Flow

```
1. User: `python -m src.main analyze --chat ru_python --date 2025-11-06`
   ↓
2. CLI → AnalyzerService.analyze(chat, date)
   ↓
3. MessageRepository.load_messages(chat, date)
   → reads ../python-tg/data/ru_python/2025-11-06.json
   ↓
4. PromptBuilder.build_summarization_prompt(messages)
   → constructs prompt with messages
   ↓
5. GigaChatClient.complete(prompt)
   → calls GigaChat API
   → logs request/response
   → tracks metrics
   ↓
6. Parse response → AnalysisResult model (Pydantic validation)
   ↓
7. AnalysisRepository.save_analysis(chat, date, result, prompt, response)
   → writes output/ru_python/2025-11-06_analysis.json
   ↓
8. Return success → display summary to user
```

### Technology Stack

| Component | Technology | Justification |
|-----------|------------|---------------|
| **Language** | Python 3.11+ | Matches tg_fetcher, modern type hints |
| **CLI Framework** | Click | Industry standard, easy to extend |
| **Data Validation** | Pydantic v2 | Type safety, validation, Settings management |
| **HTTP Client** | httpx | Async support for GigaChat API |
| **AI/LLM** | GigaChat API | Requirement (Russian LLM) |
| **Logging** | Python logging + Loki handler | Centralized logs via observability-stack |
| **Metrics** | Prometheus client | Track API usage, costs, performance |
| **Testing** | pytest | Standard, great ecosystem |
| **Code Quality** | black, isort, flake8, mypy | Enforced consistency |
| **Containerization** | Docker + docker-compose | Deployment, isolation |

---

## 🔧 Technical Decisions

### 1. Data Source Strategy
**Decision:** Read JSON files directly from `../python-tg/data/`

**Alternatives Considered:**
- Option A: Copy data files to `tg_analyzer/data/` → ❌ Duplicate data, sync issues
- Option B: API call to tg_fetcher → ❌ Overkill for MVP, adds complexity
- Option C: Shared database → ❌ Not implemented in tg_fetcher yet

**Rationale:** Simple, fast, no dependencies. Projects are on same filesystem.

**Configuration:**
```python
# src/core/config.py
class Settings(BaseSettings):
    tg_fetcher_data_path: Path = Path("../python-tg/data")
```

### 2. Message Models Reuse
**Decision:** Copy-paste Message/Chat models from tg_fetcher to `src/models/message.py`

**Why not import from tg_fetcher?**
- tg_analyzer should be independent (can deploy without tg_fetcher code)
- Models might diverge (tg_analyzer may need different fields)
- Simpler dependency management

**Trade-off:** Slight duplication vs. coupling. Choose independence.

### 3. GigaChat API Client Architecture
**Pattern:** Adapter pattern wrapping httpx

```python
# src/services/gigachat_client.py
class GigaChatClient:
    def __init__(self, api_key: str, model: str = "GigaChat"):
        self._client = httpx.AsyncClient(...)

    async def complete(self, prompt: str) -> GigaChatResponse:
        # Rate limiting, retry logic, logging
        pass
```

**Key Features:**
- Retry with exponential backoff (rate limits)
- Token counting (track costs)
- Structured logging (prompt + response)
- Metrics (latency, success rate)

### 4. Analysis Result Storage
**Format:** JSON files in `output/{chat_name}/{YYYY-MM-DD}_analysis.json`

**Schema:**
```json
{
  "version": "1.0",
  "metadata": {
    "chat": "ru_python",
    "date": "2025-11-06",
    "analyzed_at": "2025-11-07T10:30:00Z",
    "model": "GigaChat-Lite",
    "message_count": 580,
    "tokens_used": 15000,
    "analysis_duration_seconds": 12.3
  },
  "prompt": "Analyze the following messages...",
  "raw_response": "{...}",
  "analysis": {
    "discussions": [
      {
        "topic": "...",
        "keywords": [...],
        "participants": [...],
        "summary": "...",
        "expert_comment": "...",
        "message_links": [...]
      }
    ]
  }
}
```

**Why JSON?**
- Easy to read/debug
- Versionable in git
- No database overhead for MVP
- Can migrate to DB later without changing service logic

### 5. Prompt Engineering
**Strategy:** Template-based prompts with Jinja2 (or f-strings for simplicity)

**Prompt Storage:** `config/prompts/summarization.txt`

**Example Prompt Structure:**
```
You are an expert analyst of technical chat discussions.

Analyze the following Telegram chat messages from {chat_name} on {date}.

Messages ({message_count} total):
{messages_formatted}

Your task:
1. Identify main discussion topics
2. Extract keywords for each topic
3. List active participants
4. Write a summary for each topic
5. Provide expert commentary on technical quality

Output format: JSON with structure {...}
```

**Configurable Parameters:**
- Max tokens per API call
- Temperature (creativity)
- System prompt (role definition)

### 6. Observability Integration
**Logging:**
- Use observability-stack Loki handler from `infrastructure/observability-stack/python-package/`
- Structured logs (JSON format)
- Log levels: DEBUG (prompts), INFO (operations), ERROR (failures)

**Metrics (Prometheus):**
- `gigachat_api_calls_total{status="success|failure"}`
- `gigachat_api_latency_seconds{model="GigaChat"}`
- `gigachat_tokens_used_total{chat="ru_python"}`
- `analysis_duration_seconds{chat="ru_python"}`

**Grafana Dashboard:**
- API call success rate
- Token usage per day/chat
- Analysis completion times
- Cost tracking (if GigaChat has pricing per token)

### 7. Configuration Management
**Environment Variables (.env):**
```bash
GIGACHAT_API_KEY=your_key_here
GIGACHAT_BASE_URL=https://gigachat.devices.sberbank.ru/api/v1
GIGACHAT_MODEL=GigaChat-Lite
TG_FETCHER_DATA_PATH=../python-tg/data
OUTPUT_PATH=./output
LOG_LEVEL=INFO
LOKI_URL=http://localhost:3100
```

**Pydantic Settings:**
```python
class Settings(BaseSettings):
    gigachat_api_key: SecretStr
    gigachat_base_url: HttpUrl = "https://gigachat.devices.sberbank.ru/api/v1"
    gigachat_model: str = "GigaChat-Lite"

    class Config:
        env_file = ".env"
```

### 8. Error Handling Strategy
**Custom Exceptions:**
```python
class AnalyzerError(Exception):
    """Base exception"""

class DataNotFoundError(AnalyzerError):
    """JSON file not found"""

class GigaChatAPIError(AnalyzerError):
    """GigaChat API failure"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"GigaChat API error {status_code}: {message}")
```

**Retry Logic:**
- 429 (rate limit) → exponential backoff (1s, 2s, 4s, 8s)
- 500 (server error) → retry 3 times
- 401 (auth error) → fail immediately, log error
- Connection timeout → retry with longer timeout

---

## 🚀 Implementation Plan

### Phase 1: Project Setup (Day 1)
- [x] Initialize git repo, submodule observability-stack
- [ ] Create directory structure
- [ ] Create `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`
- [ ] Create `.env.example`, `.gitignore`
- [ ] Create `Dockerfile`, `docker-compose.yml`
- [ ] Create `README.md` with project description
- [ ] Setup pre-commit hooks (black, isort, flake8, mypy)
- [ ] Create `docs/PRE_IMPLEMENTATION_CHECKLIST.md`

### Phase 2: Core Models & Repository (Day 2)
- [ ] `src/models/message.py` - Message, Chat, MessageDump models
- [ ] `src/models/analysis.py` - AnalysisResult, Discussion models
- [ ] `src/models/gigachat.py` - GigaChatRequest, GigaChatResponse
- [ ] `src/repositories/message_repository.py` - load JSON dumps
- [ ] `src/repositories/analysis_repository.py` - save results
- [ ] Unit tests for models & repositories

### Phase 3: GigaChat Client (Day 3)
- [ ] `src/services/gigachat_client.py` - API wrapper
- [ ] Authentication implementation (based on GigaChat docs)
- [ ] Retry logic with exponential backoff
- [ ] Rate limiting (if docs specify limits)
- [ ] Token counting
- [ ] Structured logging (prompt/response)
- [ ] Unit tests with mocked API responses

### Phase 4: Analysis Service (Day 4)
- [ ] `src/services/prompt_builder.py` - build prompts
- [ ] `src/services/analyzer_service.py` - orchestrate analysis
- [ ] Integrate MessageRepository + GigaChatClient + AnalysisRepository
- [ ] Handle large message batches (split if needed)
- [ ] Parse GigaChat response into AnalysisResult
- [ ] Integration tests with fixture data

### Phase 5: CLI Interface (Day 5)
- [ ] `src/cli/commands.py` - Click commands
- [ ] `analyze` command with --chat, --date, --output, --model
- [ ] Progress indicators (rich library?)
- [ ] Error handling & user-friendly messages
- [ ] `src/main.py` - entry point
- [ ] Test CLI manually with real data

### Phase 6: Observability (Day 6)
- [ ] `src/utils/logger.py` - Loki integration
- [ ] `src/utils/metrics.py` - Prometheus metrics
- [ ] Update GigaChatClient to emit metrics
- [ ] Update AnalyzerService to log operations
- [ ] Create Grafana dashboard JSON
- [ ] Test with observability-stack running

### Phase 7: Docker & Deployment (Day 7)
- [ ] Dockerfile (multi-stage build)
- [ ] docker-compose.yml (analyzer + observability-stack)
- [ ] Test full Docker deployment
- [ ] Write deployment documentation
- [ ] Create quickstart.ps1 script

### Phase 8: Documentation & Testing (Day 8)
- [ ] Complete README.md
- [ ] API documentation (if adding FastAPI later)
- [ ] Usage examples
- [ ] Increase test coverage to >80%
- [ ] Run full code quality checks
- [ ] Fix all mypy/flake8 issues

---

## 📊 Success Metrics

### Technical
- ✅ 100% type hint coverage (mypy passes)
- ✅ >80% test coverage
- ✅ 0 flake8 violations
- ✅ All tests pass
- ✅ Docker build succeeds
- ✅ Pre-commit hooks configured

### Functional
- ✅ Can analyze `ru_python/2025-11-06.json` → produces valid output
- ✅ Output matches expected schema (based on `answer_ru_python_2025-11-03.json`)
- ✅ Logs visible in Loki
- ✅ Metrics visible in Prometheus/Grafana
- ✅ CLI works as expected

### Quality
- ✅ Docstrings for all public functions (Google style)
- ✅ README is comprehensive
- ✅ TZ is complete and accurate
- ✅ Code follows SOLID principles
- ✅ Error handling is robust

---

## 🔐 Security & Secrets

1. **API Keys:** Never commit to git
   - Use `.env` (gitignored)
   - Document in `.env.example`
   - Use Pydantic `SecretStr` type

2. **Dependencies:** Regular updates
   - Pin versions in `requirements.txt`
   - Check for vulnerabilities with `pip-audit`

3. **Input Validation:**
   - Validate all user inputs (chat name, date format)
   - Sanitize before using in API calls

---

## 🎯 Open Questions & Future Decisions

### MVP Scope
1. **Batch Size:** How many messages per GigaChat call?
   - Need to test token limits experimentally
   - May need to split large chats (>1000 messages)

2. **Cost Tracking:** How to calculate GigaChat costs?
   - Depends on pricing model (will know after seeing docs)
   - Store token counts for future cost estimation

3. **CLI vs API:** Should we implement both in Phase 1?
   - **Decision:** Start with CLI, add FastAPI later
   - Easier to test, simpler MVP

### Post-MVP Considerations
1. **Database Migration:** When to move from JSON to PostgreSQL?
   - Trigger: need to query/search analysis results
   - Trigger: multiple users/concurrent access

2. **Vector Search:** ChromaDB/Qdrant for semantic search?
   - Useful for finding similar discussions across dates
   - Requires embeddings generation

3. **Real-time Analysis:** Webhook from tg_fetcher?
   - Analyze messages as they're fetched
   - Requires event-driven architecture

4. **Multi-chat Analysis:** Compare multiple chats?
   - Aggregate insights from ru_python + pythonstepikchat
   - Identify cross-chat trends

---

## 📝 Notes & Decisions Log

**2025-11-07:**
- ✅ Decided to start with CLI (not API)
- ✅ JSON file storage for MVP (not database)
- ✅ Copy message models from tg_fetcher (not import)
- ✅ Use Click for CLI (not argparse)
- ✅ Use httpx for GigaChat (not requests)
- ✅ Observability integration mandatory from start
- ✅ Example output: `answer_ru_python_2025-11-03.json` as reference

**Questions Answered:**
1. GigaChat model: GigaChat-Lite (configurable)
2. Data format: one file = one chat = one day ✅
3. Result storage: JSON files with history ✅
4. Interface: CLI first, API later ✅
5. Observability: Yes, use observability-stack ✅
6. Environment: Dev only for now ✅
7. Secrets: .env file ✅

---

**Status:** Ready to implement Phase 1 (Project Setup)
**Next Step:** Create project structure and dependencies
