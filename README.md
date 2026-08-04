# ZYNTRA Platform

Unified AI platform: **multi-provider LLM gateway**, **agent runtime**, and **web shell** — designed as one coherent system, not three disconnected repos.

[![CI](https://github.com/Johanne012/zyntra-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/Johanne012/zyntra-platform/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Why this repo exists

Previous work lived in separate repositories:

| Source strength | Brought here as |
|-----------------|-----------------|
| `free-claude-gateway` | `services/gateway` — FastAPI multi-provider proxy |
| AgenticAI security patterns | `services/agents` — ownership, hashed API keys, workflows |
| FlowBrief clarity | `apps/web` — clean static/marketing + API client |

They are **linked by contracts** in `packages/shared`, one Docker Compose stack, and shared CI.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  apps/web          (UI / marketing / dashboard shell)   │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP (OpenAI-compatible + ZYNTRA APIs)
┌──────────────────────────▼──────────────────────────────┐
│  services/agents   (auth, agents, workflows, keys)      │
└──────────────────────────┬──────────────────────────────┘
                           │ internal LLM calls
┌──────────────────────────▼──────────────────────────────┐
│  services/gateway  (providers, fallback, streaming)     │
└──────────────────────────┬──────────────────────────────┘
                           │
        DeepSeek · Kimi · NIM · OpenRouter · Ollama · …
```

## Quick start

```bash
# 1. Clone
git clone https://github.com/Johanne012/zyntra-platform.git
cd zyntra-platform

# 2. Env
cp .env.example .env
# edit .env — at least one provider key

# 3. Run stack (gateway + agents + web)
docker compose up --build

# Gateway:  http://localhost:8080
# Agents:   http://localhost:8081
# Web:      http://localhost:3000
```

Local (without Docker):

```bash
# Gateway
cd services/gateway && uv sync && uv run uvicorn app.main:app --reload --port 8080

# Agents API
cd services/agents && uv sync && uv run uvicorn app.main:app --reload --port 8081

# Web (static)
cd apps/web && python -m http.server 3000
```

## Repository layout

```
zyntra-platform/
├── apps/
│   └── web/                 # Frontend shell + docs landing
├── services/
│   ├── gateway/             # Multi-provider LLM proxy (OpenAI-compatible)
│   └── agents/              # Users, API keys (hashed), agents, workflows
├── packages/
│   └── shared/              # Shared OpenAPI-ish contracts & types
├── .github/workflows/       # CI for Python services
├── docker-compose.yml
├── .env.example
├── SECURITY.md
├── CONTRIBUTING.md
└── LICENSE
```

## Core capabilities

### Gateway (`services/gateway`)
- OpenAI-compatible `/v1/chat/completions` (stream + non-stream)
- Provider registry with ordered fallback
- Health + models list
- No long-lived DB session across streams

### Agents (`services/agents`)
- API keys: `crypto`-grade random + **SHA-256 at rest** (raw key shown once)
- Ownership checks on agents / runs / notifications (IDOR-safe design)
- Workflows persistence stubs ready for expansion
- Health endpoint + security headers middleware

### Web (`apps/web`)
- Landing that documents the platform
- Simple client calling gateway health + chat demo (browser → gateway only with public/demo keys)

## Security highlights

- Secrets only via environment / Docker secrets — never commit `.env`
- API keys hashed at rest; prefix stored for display
- Ownership required for mutating agent resources
- Gateway does not log full prompts by default

See [SECURITY.md](SECURITY.md).

## License

MIT — see [LICENSE](LICENSE).
