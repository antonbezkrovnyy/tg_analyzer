# TG Analyzer - Telegram Chat Analyzer

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

Analyze Telegram chat messages using **Sber GigaChat API** (Russian LLM).

## 📋 Overview

**TG Analyzer** processes JSON dumps from [tg_fetcher](https://github.com/antonbezkrovnyy/tg_fetcher) and generates structured analysis:
- **Topic extraction**: What's being discussed
- **Summarization**: Daily chat summaries
- **Participant insights**: Who's most active
- **Expert commentary**: AI-generated technical perspectives
- **Message linking**: Direct references to original messages

## 🏗️ Architecture

```
                    ┌─────────────────────────────────────┐
                    │   Shared Infrastructure Stack       │
                    │  (c:\...\Desktop\infrastructure)    │
                    │                                     │
                    │  • Redis (Event Bus)                │
                    │  • Loki (Centralized Logging)       │
                    │  • Prometheus (Metrics Storage)     │
                    │  • Grafana (Visualization)          │
                    │  • Pushgateway (Batch Job Metrics)  │
                    └─────────────────────────────────────┘
                         ▲                          ▲
                         │                          │
            ┌────────────┴────────────┐  ┌──────────┴──────────┐
            │                         │  │                     │
    ┌───────▼──────────┐    ┌────────▼──▼─────────┐
    │   tg_fetcher     │───▶│    tg_analyzer      │
    │  (python-tg)     │    │  (this project)     │
    │                  │    │                     │
    │  Collects msgs   │    │  Analyzes via       │
    │  from Telegram   │    │  GigaChat API       │
    └──────────────────┘    └─────────────────────┘
           │                           │
           │                           │
           ▼                           ▼
    data/*.json                 output/*.json
    (messages)                  (analysis)
```

**Data Flow:**
1. `tg_fetcher` saves messages to `data/*.json`
2. `tg_analyzer` reads messages, sends to GigaChat API
3. Analysis results saved to `output/*.json`
4. Logs sent to Loki, metrics to Prometheus
5. View everything in Grafana

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- GigaChat API key ([get here](https://developers.sber.ru/gigachat))
- JSON dumps from tg_fetcher
- **Shared Infrastructure Stack running** (see below)

### Step 1: Start Shared Infrastructure

```powershell
# Navigate to infrastructure directory
cd 'c:\Users\Мой компьютер\Desktop\infrastructure'

# Start infrastructure stack
docker-compose up -d

# Verify all services are healthy
docker-compose ps
```

Expected output:
```
NAME             STATUS
tg-grafana       Up (healthy)
tg-loki          Up (healthy)
tg-prometheus    Up (healthy)
tg-pushgateway   Up (healthy)
tg-redis         Up (healthy)
```

### Step 2: Installation

**Local Development:**
```powershell
# Clone repository
git clone https://github.com/antonbezkrovnyy/tg_analyzer.git
cd tg_analyzer

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GIGACHAT_AUTH_KEY

# Install pre-commit hooks
pre-commit install
```

**Docker (Recommended):**
```powershell
# Ensure shared infrastructure is running first!
cd 'c:\Users\Мой компьютер\Desktop\infrastructure'
docker-compose ps  # All services should be healthy

# Build and run tg_analyzer
cd 'c:\Users\Мой компьютер\Desktop\tg_analyzer'
docker-compose up -d --build

# Verify connection to shared infrastructure
docker exec tg_analyzer python test_infrastructure.py
```

Expected test output:
```
============================================================
Redis               : ✅ PASSED
Loki                : ✅ PASSED
Pushgateway         : ✅ PASSED
Data Volume         : ✅ PASSED
============================================================
🎉 All tests PASSED! Infrastructure integration is working.
```

## 📖 Usage

### Docker (Production)

**Run analysis for a specific date:**
```powershell
docker-compose run --rm tg_analyzer ru_python 2025-11-08
```

**With force re-analysis:**
```powershell
docker-compose run --rm tg_analyzer ru_python 2025-11-08 --force
```

**Custom window size:**
```powershell
docker-compose run --rm tg_analyzer ru_python 2025-11-08 --window-size 100
```

### CLI Interface (Local Development)

**Analyze a chat for a specific date:**
```powershell
python -m src.cli.analyze ru_python 2025-11-08
```

**With force re-analysis:**
```powershell
python -m src.cli.analyze ru_python 2025-11-08 --force
```

**Custom window size:**
```powershell
python -m src.cli.analyze ru_python 2025-11-08 --window-size 100
```

### Output Example

Analysis results are saved as JSON:
```json
{
  "version": "1.0",
  "metadata": {
    "chat": "ru_python",
    "date": "2025-11-06",
    "analyzed_at": "2025-11-07T10:30:00Z",
    "model": "GigaChat-Lite",
    "message_count": 580,
    "tokens_used": 15000
  },
  "analysis": {
    "discussions": [
      {
        "topic": "Python Type Hints",
        "keywords": ["typing", "mypy", "annotations"],
        "participants": ["user1", "user2"],
        "summary": "Discussion about best practices...",
        "expert_comment": "Technical analysis...",
        "message_links": ["https://t.me/ru_python/123"]
      }
    ]
  }
}
```

## ⚙️ Configuration

Configure via `.env` file (see `.env.example`):

```bash
# GigaChat API
GIGACHAT_API_KEY=your_api_key_here
GIGACHAT_MODEL=GigaChat-Lite

# Data paths
TG_FETCHER_DATA_PATH=../python-tg/data
OUTPUT_PATH=./output

# Logging
LOG_LEVEL=INFO

# Observability
LOKI_URL=http://localhost:3100
PROMETHEUS_PUSHGATEWAY_URL=http://localhost:9091
```

## 🏗️ Project Structure

```
tg_analyzer/
├── src/
│   ├── cli/              # CLI commands (Click)
│   ├── core/             # Configuration, exceptions
│   ├── models/           # Pydantic data models
│   ├── repositories/     # Data access (JSON files)
│   ├── services/         # GigaChat client, analyzer
│   └── utils/            # Logging, metrics
├── tests/                # pytest tests
├── config/               # Prompts, settings
├── docs/                 # Documentation, TZ
└── output/               # Analysis results
```

## 🧪 Development

### Code Quality Tools

```powershell
# Format code
black .
isort .

# Lint
flake8 .

# Type check
mypy .

# Run tests
pytest

# Test coverage
pytest --cov=src --cov-report=html
```

### Pre-commit Hooks

Automatically run on `git commit`:
- black (formatting)
- isort (import sorting)
- flake8 (linting)
- mypy (type checking)

Install: `pre-commit install`

## 📊 Observability

Uses [observability-stack](https://github.com/antonbezkrovnyy/observability-stack) for monitoring:
- **Loki**: Centralized logging
- **Prometheus**: Metrics (API calls, latency, tokens)
- **Grafana**: Visualization dashboards

**Start observability stack:**
```powershell
cd infrastructure/observability-stack
docker-compose up -d
```

**Access:**
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100

## 🐳 Docker Deployment

**Build image:**
```powershell
docker build -t tg_analyzer:latest .
```

**Run with docker-compose:**
```powershell
docker-compose up -d
```

**View logs:**
```powershell
docker-compose logs -f tg_analyzer
```

## 📚 Documentation

- [Technical Specification](docs/tech_task/TZ-analyzer-architecture.md)
- [Pre-Implementation Checklist](docs/PRE_IMPLEMENTATION_CHECKLIST.md)
- [AI Agent Instructions](.github/copilot-instructions.md)
- [GigaChat API Docs](https://developers.sber.ru/gigachat/docs)

## 🤝 Related Projects

- [tg_fetcher](https://github.com/antonbezkrovnyy/tg_fetcher) - Telegram message collector
- [observability-stack](https://github.com/antonbezkrovnyy/observability-stack) - Shared monitoring infrastructure

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 🔗 Links

- **Author**: Anton Bezkrovnyy
- **GitHub**: https://github.com/antonbezkrovnyy/tg_analyzer
- **Issues**: https://github.com/antonbezkrovnyy/tg_analyzer/issues

---

**Status**: 🚧 In Development (v0.1.0)
**Last Updated**: November 7, 2025
