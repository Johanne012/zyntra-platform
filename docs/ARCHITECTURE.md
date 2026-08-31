# ZYNTRA Platform — System Architecture

> Last updated: 2026-08-31  
> Status: Living document (v0.4 — Data Science Team Phase 2)

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
         │              └──────────────────────┘
         │
┌────────▼────────────────────────┐
│ services/data-science-team      │
│ Supervisor + 4 specialist agents│
└─────────────────────────────────┘
```

## 2. Services

| Service | Port | Role |
|---------|------|------|
| gateway | 8080 | LLM proxy + stats |
| agents | 8081 | Generic agents CRUD + runs |
| data-science-team | 8082 | Supervisor-led DS pipeline |
| web | 3000 | Static control shell |

## 3. Data Science Team (current)

**Agents**

| Agent | Role |
|-------|------|
| `data_loader` | Load CSV / Parquet / Excel / JSON |
| `cleaner` | Drop null cols, strip strings, dedupe, median/mode impute |
| `eda` | Describe, missingness, correlations, value counts |
| `visualizer` | Histogram / bar / heatmap chart specs (JSON) |

**Default pipeline**
```
data_loader → cleaner → eda → visualizer
```

**API**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health |
| GET | `/v1/agents` | List agents |
| POST | `/v1/pipelines` | Create pipeline |
| GET | `/v1/pipelines` | List |
| GET | `/v1/pipelines/{id}` | Status + results |
| POST | `/v1/pipelines/{id}/run` | Run (file upload or path) |

## 4. Design Principles

1. Service isolation
2. Gateway as single LLM entrypoint
3. Ownership & security first
4. Observable pipelines
5. Extensible specialist teams

## 5. GitHub Actions

- `gateway` — lint + test
- `agents` — lint + test
- `data-science-team` — lint + test
- `web-structure` — required files

## 6. Roadmap

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 0 | Architecture docs | ✅ |
| 1 | Skeleton + Supervisor + Data Loader | ✅ |
| 2 | Cleaner + EDA + Visualizer | ✅ |
| 3 | Feature engineering + basic modeling | Next |
| 4 | Code generation + reproducible scripts | Planned |
| 5 | Auth reuse + persistence | Planned |
| 6 | Web UI pipeline viewer | Planned |

## 7. References

- Inspiration: https://github.com/business-science/ai-data-science-team
- `docs/DATA_SCIENCE_TEAM.md`
