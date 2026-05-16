# Architecture — AI Code Reviewer in Terminal

## System Overview

AI Code Reviewer is a terminal-first AI developer assistant built with clean
architecture principles.  It is designed to be modular, testable, and
provider-agnostic.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Layer (Typer)                        │
│  review │ security │ testgen │ commitmsg │ explain │ chat │ index│
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────▼───────────────┐
          │        Core Use Cases          │
          │  (cli/*.py orchestrates flow)  │
          └───┬───────────┬───────────────┘
              │           │
   ┌──────────▼──┐   ┌────▼────────────┐
   │  Git Module │   │  Agents Module  │
   │ diff_reader │   │  orchestrator   │
   │ repo_scanner│   │  5 specialists  │
   └──────────┬──┘   └────┬────────────┘
              │            │
   ┌──────────▼────────────▼────────────┐
   │           LLM Abstraction           │
   │   BaseLLMProvider (interface)       │
   │   OpenAIProvider │ OllamaProvider   │
   │   factory() → lru_cache singleton  │
   └──────────────┬─────────────────────┘
                  │
   ┌──────────────▼─────────────────────┐
   │          RAG Pipeline              │
   │  chunker → embedder → vector_store │
   │       ChromaDB (persistent)        │
   └──────────────┬─────────────────────┘
                  │
   ┌──────────────▼─────────────────────┐
   │        Observability               │
   │   Langfuse (traces, tokens, latency│
   │   Disk cache (diskcache, 7-day TTL)│
   └────────────────────────────────────┘
```

## Module Responsibilities

| Module | Responsibility |
|---|---|
| `app/config/settings.py` | Single source of truth for all configuration. Pydantic-settings. |
| `app/llm/` | LLM provider abstraction. `factory.py` returns cached provider singleton. |
| `app/git/` | Git diff reading and repository metadata scanning. |
| `app/prompts/` | All system + user prompt templates. Never mixes business logic. |
| `app/agents/` | Specialised review agents + LangGraph orchestrator. |
| `app/rag/` | Code chunking, embedding, ChromaDB storage, semantic retrieval. |
| `app/formatter/` | All terminal output via Rich. Never imported by business logic. |
| `app/observability/` | Langfuse tracing with no-op fallback. |
| `app/utils/` | Shared utilities: file I/O, caching, text truncation. |
| `app/cli/` | Typer command implementations. Thin orchestration only. |

## Key Design Decisions

### 1. Provider Abstraction
`BaseLLMProvider` defines a strict interface. Adding a new LLM backend
(e.g., Anthropic, Gemini) requires only implementing `complete()`, `stream()`,
and `embed()` — no other code changes needed.

### 2. Separation of Prompts
All prompts live in `app/prompts/` and return `(system, user)` tuples.
This keeps them version-controllable, testable in isolation, and easy
to A/B test across providers.

### 3. Graceful Degradation
- Langfuse disabled → silent no-op tracer
- ChromaDB empty → retriever returns `[]`
- Ollama embedding unsupported → zero-vector fallback
- Disk cache disabled → LLM always called fresh

### 4. Async Throughout
All LLM calls are `async`. CLI commands use `asyncio.run()` as the
bridge between sync Typer and async internals. Multi-agent execution
uses `asyncio.gather()` for true parallel agent execution.

### 5. Multi-Agent Pattern
```
                     ┌─────────────┐
          ┌──────────► SecurityAgent│
          │          └─────────────┘
          │          ┌──────────────────┐
          ├──────────► PerformanceAgent │
code ─────┤          └──────────────────┘
(parallel)│          ┌─────────────────┐
          ├──────────► ReadabilityAgent│
          │          └─────────────────┘
          │          ┌──────────────────┐
          ├──────────► ArchitectureAgent│
          │          └──────────────────┘
          │          ┌───────────────────┐
          └──────────► TestCoverageAgent │
                     └────────┬──────────┘
                              │
                     ┌────────▼──────────┐
                     │  Synthesis LLM   │
                     │ (executive report)│
                     └───────────────────┘
```

## Data Flow: `aicodereviewer review`

```
1. CLI parses args
2. GitDiffReader reads staged/unstaged diff → DiffResult
3. Prompt builder constructs (system, user) prompts
4. Cache lookup (SHA-256 hash of model+prompts)
5. If cache miss → LLM provider called (stream or complete)
6. Response rendered via Rich panels
7. Response cached to disk
8. Langfuse trace flushed
```

## Data Flow: `aicodereviewer index`

```
1. CLI parses repo path
2. chunk_repository() walks all source files → list[CodeChunk]
3. embed_chunks() batches to LLM embeddings API
4. VectorStore.upsert_chunks() persists to ChromaDB
5. Progress bar updates via Rich
```
