# ZYNTRA Platform — System Architecture

> Last updated: 2026-08-31  
> Status: Living document (v0.3 — Data Science Team expansion)

## 1. High-Level Overview

ZYNTRA is a **unified AI platform** monorepo that combines:

- Multi-provider LLM Gateway (OpenAI-compatible)
- Agent Runtime & management
- Web control shell
- Specialized multi-agent services (Data Science Team)

```
┌─────────────────┐
│   apps/web      │  ← Control & Monitor UI
└────────┬────────┘
         │
┌────────▼────────┐     ┌──────────────────────┐
│ services/agents │────▶│ services/gateway     │
│ (CRUD + Runs)   │     │ (LLM Proxy + Stats)  │
└────────┬────────┘     └──────────┬───────────┘
         │                         │
         │              ┌──────────▼───────────┐
         │              │   External Providers │
         │              │ OpenAI / Groq / ...  │
         │              └──────────────────────┘
         │
┌────────▼────────────────────────┐
│ services/data-science-team      │
│ Supervisor + specialized agents │
└─────────────────────────────────┘
```

## 2. Current Components

### 2.1 `services/gateway`
- OpenAI-compatible `/v1/chat/completions` proxy
- Provider load balancing + cooldown on 429
- Usage & cost statistics
- API key authentication (SHA-256 hashed)
- Port: **8080**

### 2.2 `services/agents`
- User registration & API key management
- Agent CRUD (system prompt + model)
- Agent runs (calls gateway)
- Workflows & notifications
- Ownership isolation
- Port: **8081**

### 2.3 `services/data-science-team` (NEW)
- Supervisor-led multi-agent Data Science service
- Agents: Data Loader (more coming)
- Pipeline API (create → run → inspect)
- Uses ZYNTRA Gateway for LLM calls
- Port: **8082**

### 2.4 `apps/web`
- Static shell (Console + Monitor)
- Talks to gateway & agents services

### 2.5 `packages/shared`
- Contracts and OpenAPI sketches

## 3. Design Principles

1. **Service isolation** — each service is independently deployable
2. **Gateway as single LLM entrypoint** — all agents go through it
3. **Ownership & security first** — every resource is scoped to a user
4. **Observable** — stats, runs history, notifications
5. **Extensible** — new specialized agent teams as separate services

## 4. Data Science Team — Current State

```
services/data-science-team/
├── app/
│   ├── main.py              # FastAPI (health, agents, pipelines)
│   ├── config.py
│   ├── gateway_client.py    # Talks to ZYNTRA gateway
│   ├── supervisor.py        # Routes tasks to specialists
│   ├── pipeline.py          # In-memory pipeline store
│   └── agents/
│       ├── base.py
│       └── data_loader.py   # CSV / Parquet / Excel / JSON
├── Dockerfile
├── pyproject.toml
└── tests/
```

### API (Phase 1)

| Method | Path                              | Description                |
|--------|-----------------------------------|----------------------------|
| GET    | `/health`                         | Health check               |
| GET    | `/v1/agents`                      | List available agents      |
| POST   | `/v1/pipelines`                   | Create pipeline            |
| GET    | `/v1/pipelines`                   | List pipelines             |
| GET    | `/v1/pipelines/{id}`              | Get pipeline status        |
| POST   | `/v1/pipelines/{id}/run`          | Run (file upload or path)  |

## 5. GitHub Actions

CI jobs:
- `gateway` — lint + test
- `agents` — lint + test
- `data-science-team` — lint + test
- `web-structure` — required files check

## 6. Roadmap

| Phase | Deliverable                                      | Status     |
|-------|--------------------------------------------------|------------|
| 0     | Architecture documentation                       | ✅ Done    |
| 1     | Service skeleton + Supervisor + Data Loader      | ✅ Done    |
| 2     | Cleaner + EDA + Visualizer agents                | Next       |
| 3     | Feature engineering + basic modeling             | Planned    |
| 4     | Full pipeline + code generation                  | Planned    |
| 5     | Auth reuse from agents service + persistence     | Planned    |
| 6     | Web UI integration + pipeline viewer             | Planned    |

## 7. References

- Original library inspiration: https://github.com/business-science/ai-data-science-team
- Internal: `docs/MIGRATION.md`, `docs/SECURITY_GATEWAY.md`, `docs/DATA_SCIENCE_TEAM.md`
