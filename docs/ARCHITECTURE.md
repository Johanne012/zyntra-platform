# ZYNTRA Platform — System Architecture

> Last updated: 2026-08-31  
> Status: Living document (v0.3 — Data Science Team expansion)

## 1. High-Level Overview

ZYNTRA is a **unified AI platform** monorepo that combines:

- Multi-provider LLM Gateway (OpenAI-compatible)
- Agent Runtime & management
- Web control shell
- Specialized multi-agent services (starting with Data Science Team)

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
│ services/data-science-team      │  ← NEW
│ Supervisor-led multi-agent DS   │
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

### 2.3 `apps/web`
- Static shell (Console + Monitor)
- Talks to gateway & agents services

### 2.4 `packages/shared`
- Contracts and OpenAPI sketches

## 3. Design Principles

1. **Service isolation** — each service is independently deployable
2. **Gateway as single LLM entrypoint** — all agents go through it
3. **Ownership & security first** — every resource is scoped to a user
4. **Observable** — stats, runs history, notifications
5. **Extensible** — new specialized agent teams as separate services

## 4. Expansion: Data Science Team

### Goal
Integrate a **Supervisor-led multi-agent Data Science team** based on the open-source project  
[business-science/ai-data-science-team](https://github.com/business-science/ai-data-science-team).

### Target Architecture (after integration)

```
services/data-science-team/
├── app/
│   ├── main.py                 # FastAPI entry
│   ├── supervisor.py           # Routes tasks to specialists
│   ├── agents/                 # Specialized agents
│   │   ├── data_loader.py
│   │   ├── cleaner.py
│   │   ├── eda.py
│   │   ├── visualizer.py
│   │   ├── feature_engineer.py
│   │   └── modeler.py          # H2O / sklearn
│   ├── pipeline.py             # Reproducible pipeline tracking
│   ├── gateway_client.py       # Talks to ZYNTRA gateway
│   └── security.py
├── Dockerfile
├── pyproject.toml
└── tests/
```

### Integration Points

| Concern              | Decision                                      |
|----------------------|-----------------------------------------------|
| LLM calls            | Always via `services/gateway`                 |
| Auth                 | Reuse ZYNTRA API keys (Bearer)                |
| Data storage         | Local volume + optional object storage later  |
| Pipeline state       | In-memory + persisted JSON / MLflow optional  |
| Port                 | 8082                                          |
| CI                   | Added to existing GitHub Actions workflow     |

### Capabilities (Phase 1)

- Load CSV / Parquet / Excel
- Clean & wrangle data
- Automated EDA + reports
- Visualization generation
- Feature engineering
- Basic AutoML (H2O or sklearn)
- Full reproducible pipeline + generated Python code

## 5. GitHub Actions Strategy

Current CI already covers gateway + agents.

**New jobs to add:**

- `data-science-team` — lint + unit tests
- Optional: build & push Docker image on `main`
- Structure checks for new service files

## 6. Roadmap

| Phase | Deliverable                                      | Status     |
|-------|--------------------------------------------------|------------|
| 0     | Architecture documentation                       | ✅ Done    |
| 1     | Service skeleton + health endpoint               | Next       |
| 2     | Supervisor + core agents (load/clean/EDA)        | Planned    |
| 3     | Full pipeline + code generation                  | Planned    |
| 4     | Web UI integration + pipeline viewer             | Planned    |
| 5     | Production hardening (sandbox, quotas)           | Planned    |

## 7. References

- Original library: https://github.com/business-science/ai-data-science-team
- Internal: `docs/MIGRATION.md`, `docs/SECURITY_GATEWAY.md`
