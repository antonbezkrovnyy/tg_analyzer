# Pre-Implementation Checklist

**Purpose:** Verify all requirements before writing code to prevent missing critical dependencies.

**Usage:** Check this file BEFORE implementing ANY feature in tg_analyzer.

---

## ✅ General Project Requirements

### Code Quality (MANDATORY)
- [ ] **Type Hints**: All function signatures have type annotations
- [ ] **Docstrings**: All public functions/classes have Google-style docstrings
- [ ] **Pydantic**: Use for data validation (models, settings)
- [ ] **Error Handling**: Specific exceptions, never bare `except:`
- [ ] **Logging**: Use `logging` module with Loki handler, not `print()`

### Tools Configuration
- [ ] **black**: Code formatting (line length: 88)
- [ ] **isort**: Import sorting (stdlib → third-party → local)
- [ ] **flake8**: Linting
- [ ] **mypy**: Type checking (strict mode)
- [ ] **pre-commit**: Hooks for all above tools

### Project Structure
- [ ] **pyproject.toml**: Project metadata, tool configs
- [ ] **requirements.txt**: Production dependencies (pinned versions)
- [ ] **requirements-dev.txt**: Dev dependencies (black, pytest, etc.)
- [ ] **.env.example**: Document all env variables
- [ ] **.gitignore**: Exclude .venv, __pycache__, .env, output/

---

## ✅ TG Analyzer Specific Requirements

### Data Models (Pydantic)
- [ ] **Message Model**: Reuse schema from tg_fetcher
  - `id`, `date`, `text`, `sender_id`, `reply_to_msg_id`, `reactions`, `comments`
- [ ] **MessageDump Model**: Top-level structure
  - `version`, `source_info`, `senders`, `messages`
- [ ] **AnalysisResult Model**: Output schema
  - `version`, `metadata`, `prompt`, `raw_response`, `analysis`
  - `discussions[]` with `topic`, `keywords`, `participants`, `summary`, `expert_comment`, `message_links`
- [ ] **GigaChat Models**: Request/response schemas
  - Based on GigaChat API docs (TBD when docs provided)

### GigaChat API Integration
- [ ] **Authentication**: Implement based on GigaChat docs
  - API key via environment variable `GIGACHAT_API_KEY`
  - SecretStr type in Pydantic Settings
- [ ] **Rate Limiting**: Implement retry with exponential backoff
  - Handle 429 (Too Many Requests)
  - Configurable max retries and delays
- [ ] **Error Handling**: Specific exceptions
  - `GigaChatAPIError`, `GigaChatAuthError`, `GigaChatRateLimitError`
- [ ] **Token Counting**: Track tokens used for cost estimation
- [ ] **Logging**: Log ALL API calls (prompt, response, latency, tokens)

### Repository Pattern
- [ ] **MessageRepository**: Read JSON dumps
  - `load_messages(chat: str, date: str) -> MessageDump`
  - Handle FileNotFoundError gracefully
  - Validate JSON schema with Pydantic
- [ ] **AnalysisRepository**: Save analysis results
  - `save_analysis(chat: str, date: str, result: AnalysisResult) -> Path`
  - Create output directories if not exist
  - Don't overwrite (append timestamp if file exists)

### Service Layer
- [ ] **GigaChatClient**: API wrapper
  - Async methods (use httpx.AsyncClient)
  - Retry logic
  - Metrics emission
  - Structured logging
- [ ] **AnalyzerService**: Orchestration
  - Load messages → build prompt → call GigaChat → parse response → save result
  - Handle large message batches (split if needed)
  - Progress tracking (optional: rich library)
- [ ] **PromptBuilder**: Construct prompts
  - Template-based (config/prompts/summarization.txt)
  - Format messages for context
  - Include metadata (chat name, date, message count)

### Observability Stack Integration
- [ ] **Logging**:
  - Use observability-stack Loki handler
  - Structured logs (JSON format)
  - Include correlation IDs (chat + date as ID)
  - Log levels: DEBUG (prompts/responses), INFO (operations), ERROR (failures)
- [ ] **Metrics** (Prometheus):
  - `gigachat_api_calls_total{status, model}`
  - `gigachat_api_latency_seconds{model}`
  - `gigachat_tokens_used_total{chat, model}`
  - `analysis_duration_seconds{chat}`
  - `analysis_errors_total{error_type}`
- [ ] **Grafana Dashboard**: Create JSON config
  - API success rate panel
  - Token usage over time
  - Analysis latency histogram
  - Error rate panel

### CLI Interface (Click)
- [ ] **Commands**:
  - `analyze --chat <name> --date <YYYY-MM-DD> [--output <path>] [--model <name>]`
  - Input validation (date format, chat exists)
  - User-friendly error messages
  - Progress indicators (optional)
- [ ] **Configuration**:
  - Load from .env (Pydantic Settings)
  - Allow overrides via CLI flags
- [ ] **Help Text**: Comprehensive --help messages

### Docker Setup
- [ ] **Dockerfile**:
  - Multi-stage build (build + runtime)
  - Python 3.11+ base image
  - Install dependencies from requirements.txt
  - Non-root user for security
  - Copy source code
  - Set entry point to CLI
- [ ] **docker-compose.yml**:
  - Service: tg_analyzer
  - Volumes: mount data/, output/
  - Environment: load from .env
  - Network: connect to observability-stack
  - Optional: depends_on observability services

### Testing
- [ ] **Unit Tests**:
  - Models: Pydantic validation
  - Repositories: File I/O with fixtures
  - GigaChatClient: Mocked API responses
  - PromptBuilder: Template rendering
- [ ] **Integration Tests**:
  - Full analysis flow with fixture data
  - GigaChatClient with real API (manual/optional)
- [ ] **Test Coverage**: >80% target
- [ ] **Fixtures**:
  - `tests/fixtures/sample_messages.json`
  - `tests/fixtures/sample_analysis.json`
  - Mock GigaChat responses

### Documentation
- [ ] **README.md**:
  - Project description
  - Installation (local + Docker)
  - Usage examples
  - Configuration (env variables)
  - Architecture overview (link to TZ)
- [ ] **TZ (This File)**: Complete and up-to-date
- [ ] **API Docs**: If FastAPI is added later
- [ ] **Code Comments**: Complex logic explained
- [ ] **Docstrings**: All public functions/classes

### Security
- [ ] **Secrets Management**:
  - Never commit .env
  - Use .env.example with placeholders
  - Use Pydantic SecretStr for sensitive values
- [ ] **Input Validation**:
  - Validate chat names (prevent path traversal)
  - Validate date format (YYYY-MM-DD)
  - Sanitize before using in file paths/API calls
- [ ] **Dependencies**:
  - Pin versions in requirements.txt
  - Run pip-audit for vulnerabilities

---

## ✅ Before Starting Each Phase

### Phase 1: Project Setup
- [ ] Read TZ-analyzer-architecture.md fully
- [ ] Verify all directories in structure exist
- [ ] Verify all config files created (.env.example, pyproject.toml, etc.)
- [ ] Verify pre-commit hooks installed and working
- [ ] Run `black . && isort . && flake8 . && mypy .` - all pass (or no files yet)

### Phase 2: Core Models & Repository
- [ ] Check tg_fetcher message schema matches expectations
- [ ] Verify example output (answer_ru_python_2025-11-03.json) for AnalysisResult schema
- [ ] Plan Pydantic validators for date formats, URL formats, etc.
- [ ] Create test fixtures BEFORE implementing logic

### Phase 3: GigaChat Client
- [ ] **CRITICAL**: Get GigaChat API documentation from user
- [ ] Understand authentication flow (OAuth vs API key)
- [ ] Understand rate limits (requests/minute, tokens/day)
- [ ] Understand request/response schema
- [ ] Understand error codes and retry strategy
- [ ] Plan token counting logic
- [ ] Create mock responses for testing

### Phase 4: Analysis Service
- [ ] Design prompt template (review with user)
- [ ] Plan message batching strategy (token limit per request)
- [ ] Plan response parsing (what if GigaChat returns invalid JSON?)
- [ ] Decide on fallback behavior (partial results? fail fast?)

### Phase 5: CLI Interface
- [ ] Design command structure (review with user)
- [ ] Plan interactive mode (if needed)
- [ ] Plan progress indicators (simple print vs rich library)

### Phase 6: Observability
- [ ] Verify observability-stack is running
- [ ] Test Loki handler with sample logs
- [ ] Test Prometheus pushgateway with sample metrics
- [ ] Create Grafana dashboard JSON

### Phase 7: Docker & Deployment
- [ ] Test Dockerfile builds successfully
- [ ] Test docker-compose up with all services
- [ ] Verify volumes mount correctly (data/, output/)
- [ ] Verify environment variables load correctly

### Phase 8: Documentation & Testing
- [ ] Review all docstrings for completeness
- [ ] Review README for clarity (ask user if unclear)
- [ ] Run full test suite
- [ ] Check test coverage report
- [ ] Fix all code quality issues

---

## 🚨 Red Flags - STOP Implementation If:

- [ ] **No GigaChat API docs provided yet** → Cannot implement client correctly
- [ ] **Unclear prompt design** → Ask user for example or requirements
- [ ] **No example output** → Cannot validate AnalysisResult schema
- [ ] **Observability-stack not set up** → Cannot test logging/metrics
- [ ] **Type hints missing** → Add them before proceeding
- [ ] **Tests failing** → Fix before adding new features
- [ ] **Mypy errors** → Fix before proceeding
- [ ] **No .env.example** → Security risk, create it

---

## 📋 Batch Questions Template (Use Before Implementation)

When starting a new phase, ask ALL these questions at once:

```markdown
## 🤔 Уточняющие вопросы по [Phase Name]:

1. **[Category 1]**: Question?
2. **[Category 2]**: Question?
3. **[Category 3]**: Question?

## 📋 Предлагаемый подход:

1. Step 1
2. Step 2
3. Step 3

**Подходит? Мне начинать?**
```

---

## 🎯 Quality Gates (Every Commit)

Before committing ANY code:
- [ ] `black .` - passes
- [ ] `isort .` - passes
- [ ] `flake8 .` - 0 violations
- [ ] `mypy .` - 0 errors
- [ ] `pytest` - all tests pass
- [ ] Docstrings added for new functions
- [ ] Type hints added for new functions
- [ ] Updated docs/console.log if ran terminal commands
- [ ] Updated TZ if made architectural decisions

---

**Last Updated:** November 7, 2025
**Status:** Ready to use for implementation phases
