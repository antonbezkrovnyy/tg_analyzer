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
tg_fetcher → JSON dumps → tg_analyzer → GigaChat API → Analysis Results
                                     ↓
                         observability-stack (logs/metrics)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- GigaChat API key ([get here](https://developers.sber.ru/gigachat))
- JSON dumps from tg_fetcher

### Installation

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
# Edit .env and add your GIGACHAT_API_KEY

# Install pre-commit hooks
pre-commit install
```

**Docker:**
```powershell
# Build and run
docker-compose up --build
```

## 📖 Usage

### CLI Interface

**Analyze a chat for a specific date:**
```powershell
python -m src.main analyze --chat ru_python --date 2025-11-06
```

**With custom output path:**
```powershell
python -m src.main analyze --chat ru_python --date 2025-11-06 --output ./results/
```

**Using different GigaChat model:**
```powershell
python -m src.main analyze --chat ru_python --date 2025-11-06 --model GigaChat-Plus
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
