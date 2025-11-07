# Context for AI Assistant - TG Analyzer Project

## 📋 Project Overview

**Project Name:** `tg_analyzer` - Telegram Chat Analyzer
**Location:** `c:\Users\Мой компьютер\Desktop\tg_analyzer`
**Created:** November 7, 2025
**Repository:** Not yet created on GitHub (will be `antonbezkrovnyy/tg_analyzer`)

This is the **second service** in the Telegram data processing pipeline:
1. **tg_fetcher** (completed) - collects messages from Telegram chats
2. **tg_analyzer** (this project) - analyzes collected messages using AI

## 🎯 Project Purpose

Analyze Telegram chat messages collected by `tg_fetcher` using **Sber GigaChat API** (Russian LLM).

**Input:** JSON dumps from `tg_fetcher` (located in `../python-tg/data/`)
**Output:** Analysis results (format TBD - depends on use case)
**Interface:** Flexible architecture supporting both API and CLI

## 🏗️ Project Structure (Current State)

```
tg_analyzer/
├── .git/                          # Git repository initialized
├── .github/                       # Copied from tg_fetcher
│   ├── copilot-instructions.md    # AI agent operational rules
│   └── instructions/
│       └── always.instructions.md # Critical workflow rules
├── .gitmodules                    # Git submodules config
├── infrastructure/
│   └── observability-stack/       # Git submodule from antonbezkrovnyy/observability-stack
├── src/                           # ✅ Source code structure
│   ├── __init__.py
│   ├── cli/                       # CLI commands (Click)
│   ├── core/                      # Config, exceptions
│   ├── models/                    # Pydantic models
│   ├── repositories/              # Data access
│   ├── services/                  # GigaChat client, analyzer
│   └── utils/                     # Logging, metrics
├── tests/                         # ✅ Test structure
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/                          # ✅ Documentation
│   ├── tech_task/
│   │   └── TZ-analyzer-architecture.md
│   ├── PRE_IMPLEMENTATION_CHECKLIST.md
│   ├── PROJECT_SETUP_SUMMARY.md
│   └── console.log
├── config/                        # ✅ Configuration
│   └── prompts/
├── output/                        # ✅ Analysis results (gitignored)
├── scripts/                       # ✅ Setup scripts
│   └── quickstart.ps1
├── .env.example                   # ✅ Environment template
├── .gitignore                     # ✅ Git ignore rules
├── .pre-commit-config.yaml        # ✅ Pre-commit hooks
├── Dockerfile                     # ✅ Docker image
├── docker-compose.yml             # ✅ Multi-container setup
├── pyproject.toml                 # ✅ Project metadata + tool configs
├── requirements.txt               # ✅ Production dependencies
├── requirements-dev.txt           # ✅ Dev dependencies
├── README.md                      # ✅ Project documentation
└── CONTEXT_FOR_AI.md              # This file
```

**Status:** ✅ **Phase 1 Complete** - Full project structure created, ready for implementation.

## 🔗 Dependencies & Related Projects

### 1. tg_fetcher (Sibling Project)
- **Location:** `c:\Users\Мой компьютер\Desktop\python-tg`
- **GitHub:** https://github.com/antonbezkrovnyy/tg_fetcher
- **Purpose:** Fetches messages from Telegram chats, saves as JSON
- **Data Location:** `../python-tg/data/`
  - `ru_python/2025-11-05.json`, `2025-11-06.json` (580 messages on Nov 6)
  - `pythonstepikchat/2025-11-05.json`, `2025-11-06.json` (169 messages on Nov 6)
- **Message Schema (v1.0):**
  ```json
  {
    "version": "1.0",
    "metadata": {
      "source": "@ru_python",
      "date": "2025-11-06",
      "fetched_at": "2025-11-07T08:28:15.123456+03:00",
      "message_count": 580
    },
    "messages": [
      {
        "id": 123,
        "date": "2025-11-06T10:15:30+03:00",
        "text": "Message content",
        "sender_id": 456,
        "views": 100,
        "forwards": 5,
        "replies": null
      }
    ]
  }
  ```

**Decision:** `tg_fetcher` dependency strategy TBD (git URL, local path, or just read data files directly?)

### 2. observability-stack (Shared Infrastructure)
- **Location:** `infrastructure/observability-stack` (git submodule)
- **GitHub:** https://github.com/antonbezkrovnyy/observability-stack
- **Purpose:** Centralized logging (Loki), metrics (Prometheus), visualization (Grafana)
- **Status:** Already used by tg_fetcher, will be shared with tg_analyzer
- **Integration:** Docker Compose, Loki handler for Python logging, Prometheus metrics

**Note:** Since both projects use observability-stack, consider:
- Running observability-stack once for both services
- Or each service connects to the same observability endpoints

## 🧠 GigaChat Integration (Main Feature)

**API:** Sber GigaChat - https://developers.sber.ru/gigachat
**Purpose:** Analyze Russian-language Telegram messages

**Potential Analysis Types:**
- Sentiment analysis (позитив/негатив/нейтральный)
- Topic extraction (о чем говорят в чате)
- Summarization (краткое содержание за день/неделю)
- Question detection (выделение вопросов для FAQ)
- Trending topics (популярные темы)
- Spam/toxic message detection

**Authentication:** Requires GigaChat API key (stored in environment variables)

## 📚 Key Documentation to Follow

**CRITICAL:** Before implementing ANY code, read:
1. `.github/copilot-instructions.md` - Full operational rules for AI agent
2. `.github/instructions/always.instructions.md` - Critical workflow checklist

**Key Rules Summary:**
- ✅ **ASK QUESTIONS FIRST** - Never write code without clarifying requirements
- ✅ **CREATE TZ** - Write technical specification before implementation (`docs/tech_task/TZ-<feature>.md`)
- ✅ **BATCH ALL QUESTIONS** - Ask everything at once, not sequentially
- ✅ **LOG COMMANDS** - Every `run_in_terminal` → `docs/console.log`
- ✅ **TYPE HINTS + DOCSTRINGS** - Mandatory for all functions
- ✅ **CODE QUALITY** - black, isort, flake8, mypy, pre-commit hooks

## 🛠️ Technology Stack (Expected)

Based on tg_fetcher conventions:
- **Python:** 3.11+
- **Framework:** TBD (FastAPI for API? Click for CLI?)
- **Data Validation:** Pydantic v2
- **AI/LLM:** GigaChat API client
- **Observability:** Loki (logs), Prometheus (metrics), Grafana
- **Containerization:** Docker + docker-compose
- **Code Quality:** black, isort, flake8, mypy, pre-commit
- **Testing:** pytest

## 📝 Implementation Status

### ✅ Completed:
1. **Phase 1: Project Structure Setup** (November 7, 2025)
   - ✅ Full directory structure
   - ✅ Configuration files (pyproject.toml, requirements, .env.example, etc.)
   - ✅ Docker setup (Dockerfile, docker-compose.yml)
   - ✅ Documentation (README, TZ, Checklist, Summary)
   - ✅ Pre-commit hooks configuration
   - ✅ Quick start script

2. **Technical Specification**
   - ✅ Complete TZ: `docs/tech_task/TZ-analyzer-architecture.md`
   - ✅ All architecture decisions documented
   - ✅ Data flow defined
   - ✅ Output format specified (based on `answer_ru_python_2025-11-03.json`)

### 📌 Next Steps:
**Phase 2: Core Models & Repository**
1. Data models (Pydantic)
   - Message, MessageDump (from tg_fetcher schema)
   - AnalysisResult, Discussion (output schema)
   - GigaChatRequest, GigaChatResponse ⚠️ **BLOCKED: Need API docs**

2. Repositories
   - MessageRepository (read JSON dumps)
   - AnalysisRepository (save results)

3. Unit tests
   - Create fixtures
   - Test model validation
   - Test file I/O

### ⚠️ Blockers:
- **GigaChat API Documentation**: Required to implement client and models
  - Need: Authentication flow, request/response schema, rate limits, error codes

## 🚀 How to Continue This Project

**When starting new chat with AI:**

```
Привет! Я продолжаю работу над проектом tg_analyzer - анализатор Telegram чатов.

Прочитай пожалуйста CONTEXT_FOR_AI.md в корне проекта, а также .github/copilot-instructions.md
и .github/instructions/always.instructions.md для понимания правил работы.

Проект только создан, есть базовая структура (.github, observability-stack submodule).

Текущая задача: [опиши что нужно сделать]

Вопросы:
- [твои вопросы, если есть]
```

**Important Context Files:**
- `CONTEXT_FOR_AI.md` - this file (project overview)
- `.github/copilot-instructions.md` - AI operational rules
- `.github/instructions/always.instructions.md` - critical workflow checklist
- `../python-tg/README.md` - tg_fetcher project (reference for conventions)
- `../python-tg/docs/tech_task/TZ-telegram-fetcher.md` - example TZ structure

## 🔑 Environment Variables (Future)

```bash
# GigaChat API
GIGACHAT_API_KEY=your_api_key_here
GIGACHAT_BASE_URL=https://gigachat.devices.sberbank.ru/api/v1

# Data Sources
TG_FETCHER_DATA_PATH=../python-tg/data

# Observability
LOKI_URL=http://localhost:3100
PROMETHEUS_PUSHGATEWAY_URL=http://localhost:9091

# Application
LOG_LEVEL=INFO
```

## 📊 Success Criteria

Project is ready when:
- ✅ Can read JSON dumps from tg_fetcher
- ✅ Can analyze messages using GigaChat API
- ✅ Provides useful insights (sentiment, topics, summary)
- ✅ Has both CLI and API interfaces
- ✅ Integrates with observability-stack
- ✅ Has comprehensive tests (>80% coverage)
- ✅ All code quality checks pass (black, isort, flake8, mypy)
- ✅ Documented (README, TZ, API docs, docstrings)
- ✅ Dockerized and ready for deployment

## 🎓 Lessons from tg_fetcher Project

Apply these learnings:
1. **Progress Tracking:** Implement from the start (avoid re-processing data)
2. **One-shot Mode:** Support both continuous and one-time analysis runs
3. **Configuration:** Use Pydantic Settings for type-safe config
4. **Error Handling:** Specific exceptions with context, comprehensive logging
5. **Type Safety:** 100% type hint coverage, mypy validation
6. **Documentation:** TZ before code, docstrings for all public functions
7. **Observability:** Structured logging, metrics from day one
8. **Testing:** Write tests alongside features, not after

## 🤝 Integration with tg_fetcher

**Data Flow:**
```
tg_fetcher → JSON dumps (data/*.json)
             ↓
tg_analyzer reads → GigaChat API → Analysis results
             ↓
observability-stack (shared logs/metrics)
```

**Potential Integration Points:**
- Read JSON files directly (filesystem)
- Future: API endpoint to fetch data from tg_fetcher
- Future: Shared database for both services

---

**Last Updated:** November 7, 2025
**Status:** Project initialized, awaiting full implementation
**Next Chat:** Start with reading this file + .github instructions, then ask clarifying questions before implementing
