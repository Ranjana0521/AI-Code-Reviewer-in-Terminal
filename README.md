<div align="center">

# 🤖 AI Code Reviewer in Terminal

**A production-grade AI-powered developer assistant for the terminal.**
Reads git diffs · Reviews code · Detects bugs & vulnerabilities · Generates tests & commit messages · Supports RAG · Multi-agent workflows · Beautiful terminal UI

---

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Tests](https://img.shields.io/badge/tests-pytest-green)](tests/)
[![OpenAI](https://img.shields.io/badge/LLM-OpenAI%20%7C%20Ollama-purple)](https://openai.com)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](Dockerfile)

</div>

---

## ✨ What Is This?

**AI Code Reviewer** is a powerful terminal-first AI assistant — similar to GitHub Copilot CLI, CodeRabbit, and Cursor AI — but running entirely in your terminal with full local LLM support via Ollama.

It integrates **5 specialised AI agents**, a **RAG pipeline** for repository-aware context, **beautiful Rich terminal UI**, and **Langfuse observability** into a single `pip install` CLI tool.

---

## 🎯 Features

| Feature | Command | Description |
|---|---|---|
| 📋 **Full Code Review** | `review` | Bugs, security, perf, readability, architecture |
| 🔒 **Security Audit** | `security` | OWASP Top 10, CWE findings, severity ratings |
| 🧪 **Test Generator** | `testgen` | Pytest suites with mocks, edge cases, parametrize |
| 💬 **Commit Messages** | `commitmsg` | Conventional Commits in 3 tiers |
| 💡 **Code Explain** | `explain <file>` | Plain-English file explanation + architecture |
| 🗨️ **Interactive Chat** | `chat` | RAG-powered chat about your codebase |
| 📚 **Repo Indexing** | `index` | Embed repo into ChromaDB for RAG retrieval |
| 🤖 **Multi-Agent** | `review --agents` | 5 parallel specialist agents + synthesis |

---

## 🏗️ Architecture

```
aicodereviewer/
│
├── app/
│   ├── cli/              # Typer CLI commands (review, security, testgen…)
│   ├── agents/           # 5 specialist agents + LangGraph orchestrator
│   ├── rag/              # ChromaDB embeddings pipeline
│   ├── llm/              # OpenAI + Ollama provider abstraction
│   ├── git/              # GitPython diff reader + repo scanner
│   ├── prompts/          # All LLM prompt templates
│   ├── formatter/        # Rich terminal UI components
│   ├── observability/    # Langfuse tracing
│   ├── config/           # Pydantic settings
│   ├── utils/            # Cache, file utilities
│   └── main.py           # Typer root app
│
├── tests/                # pytest test suite
├── docs/                 # Architecture docs
├── .github/workflows/    # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

> See [`docs/architecture.md`](docs/architecture.md) for full diagrams and data-flow walkthroughs.

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourname/aicodereviewer.git
cd aicodereviewer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows

# Install
pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

### 3. Verify Installation

```bash
aicodereviewer --help
aicodereviewer --version
```

---

## ⚙️ Configuration

All settings live in `.env` (copy from `.env.example`):

```env
# LLM Provider: openai | ollama
MODEL_PROVIDER=openai

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Langfuse Observability (optional)
LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# Behaviour
MAX_DIFF_LINES=500
STREAM_RESPONSES=true
CACHE_ENABLED=true
```

---

## 📖 Commands

### `review` — AI Code Review

```bash
# Review staged changes
git add .
aicodereviewer review

# Review unstaged changes
aicodereviewer review --unstaged

# Review a commit range
aicodereviewer review --base HEAD~3 --head HEAD

# Run 5 parallel specialist agents
aicodereviewer review --agents

# Skip cache
aicodereviewer review --no-cache
```

**Output sections:**
- 🐛 Bugs & Logic Errors
- 🔒 Security Vulnerabilities
- ⚡ Performance Issues
- 📖 Readability & Style
- 🏗️ Architecture & Design
- ✅ Best Practices
- 💡 Overall Verdict (HIGH/MEDIUM/LOW risk)

---

### `security` — Dedicated Security Audit

```bash
# Audit staged diff
aicodereviewer security

# Audit a specific file
aicodereviewer security app/auth.py
```

Detects: SQL injection, hardcoded secrets, insecure auth, path traversal,
unsafe deserialization, SSRF, weak cryptography, and more.

---

### `testgen` — Unit Test Generator

```bash
# Generate tests for staged diff
aicodereviewer testgen

# Generate tests for a specific file
aicodereviewer testgen app/services/user_service.py

# Save to file
aicodereviewer testgen app/utils.py --output tests/test_utils.py
```

Generates: happy-path, edge-case, error-path, and mock-heavy tests with
`pytest.mark.parametrize` where applicable.

---

### `commitmsg` — Commit Message Generator

```bash
git add .
aicodereviewer commitmsg

# Copy minimal message to clipboard (Windows)
aicodereviewer commitmsg --copy
```

Output example:
```
1. Minimal:
   feat(auth): add JWT refresh token rotation

2. Standard:
   feat(auth): add JWT refresh token rotation

   Implements automatic refresh token rotation on each use to prevent
   token replay attacks. Tokens are invalidated server-side on rotation.

3. Detailed:
   feat(auth): add JWT refresh token rotation
   ...
   CHANGELOG:
   - Added TokenRotationService with atomic swap logic
   - Added refresh_token endpoint with 7-day expiry
   - Closes #142
```

---

### `explain` — Code Explanation

```bash
aicodereviewer explain app/main.py
aicodereviewer explain app/agents/orchestrator.py
```

Output: what the file does, architecture role, code flow, key functions,
config/side effects, and gotchas — all in plain English.

---

### `chat` — Interactive Chat Mode

```bash
# Chat with RAG context from your indexed repo
aicodereviewer chat

# Chat without RAG
aicodereviewer chat --no-rag
```

Ask anything about your codebase:
```
You: How does the authentication flow work?
AI: Based on your repository, the authentication flow starts in...
```

---

### `index` — Repository RAG Indexing

```bash
# Index current repo
aicodereviewer index

# Index a different repo
aicodereviewer index --repo /path/to/other/repo

# Clear and re-index
aicodereviewer index --clear
```

---

## 🤖 Multi-Agent Review

The `--agents` flag activates 5 independent specialist agents running in parallel:

```
┌─────────────────────┐
│   Your Git Diff     │
└──────────┬──────────┘
           │ (parallel asyncio.gather)
     ┌─────┴─────┬──────────┬──────────┬─────────────┐
     ▼           ▼          ▼          ▼             ▼
 Security    Performance Readability Architecture Test Coverage
  Agent       Agent       Agent       Agent          Agent
     └─────┬─────┴──────────┴──────────┴─────────────┘
           │
     ┌─────▼─────────────────────┐
     │  Synthesis LLM Call       │
     │  → Executive Summary      │
     │  → Top Priority Issues    │
     │  → Strengths              │
     │  → Action Items           │
     └───────────────────────────┘
```

---

## 🧠 RAG Pipeline

```bash
# Step 1: Index your repo (once)
aicodereviewer index

# Step 2: All subsequent commands automatically use context
aicodereviewer review       # review with repo awareness
aicodereviewer chat         # chat with codebase knowledge
```

The RAG pipeline:
1. Chunks all source files into 60-line overlapping windows
2. Generates OpenAI embeddings for each chunk
3. Stores in ChromaDB (persisted to `.chroma_db/`)
4. At query time, embeds the question and retrieves top-N similar chunks

---

## 🦙 Local LLM with Ollama

```bash
# Install Ollama: https://ollama.ai
ollama pull llama3
# or: ollama pull codellama
# or: ollama pull mistral

# Switch to Ollama in .env
MODEL_PROVIDER=ollama
OLLAMA_MODEL=llama3

aicodereviewer review   # now uses local Ollama
```

---

## 🐳 Docker

```bash
# Build and run
docker build -t aicodereviewer .
docker run --rm -it \
  -v $(pwd):/workspace \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  aicodereviewer review

# Or with Docker Compose (includes ChromaDB + Ollama)
docker-compose up
docker-compose run aicodereviewer review
```

---

## 🔭 Observability (Langfuse)

```env
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

Tracks: prompt content · token usage · latency per call · errors · model versions

---

## 🧪 Running Tests

```bash
pip install -e ".[dev]"

# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_agents.py -v
```

---

## 🗺️ Roadmap

- [x] Git diff review (staged/unstaged/range)
- [x] Security audit
- [x] Unit test generator
- [x] Commit message generator
- [x] Code explanation
- [x] Multi-agent orchestration (LangGraph)
- [x] Repository RAG with ChromaDB
- [x] Ollama local LLM support
- [x] Beautiful Rich terminal UI
- [x] Langfuse observability
- [x] Disk caching
- [x] Interactive chat mode
- [x] Docker support
- [x] CI/CD (GitHub Actions)
- [ ] GitHub PR review bot (webhook server)
- [ ] AI auto-fix with git apply
- [ ] Voice review mode
- [ ] Repository summary command
- [ ] VSCode extension

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make changes and add tests
4. Run `pytest` and `ruff check .`
5. Commit using `aicodereviewer commitmsg` 😄
6. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
Built with ❤️ using Python · Typer · Rich · OpenAI · LangGraph · ChromaDB
</div>
