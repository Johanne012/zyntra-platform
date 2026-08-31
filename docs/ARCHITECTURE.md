# ZYNTRA Platform — System Architecture

> Last updated: 2026-08-31  
> Status: Living document (v0.4 — Data Science Team Phase 2)

## 1. High-Level Overview

ZYNTRA is a **unified AI platform** monorepo that combines:

- Multi-provider LLM Gateway (OpenAI-compatible)
- Agent Runtime & management
- Web control shell
- Specialized multi-agent Data Science Team

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
│ Supervisor + 4 specialized agents│
└─────────────────────────────────┘
```

## 2. Services

| Service              | Port | Role                                      |
|----------------------|------|-------------------------------------------|
| gateway              | 8080 | LLM proxy, balancing, stats               |
| agents               | 8081 | Generic agents CRUD + runs                |
| data-science-team    | 8082 | Supervisor-led DS pipeline                |
| web                  | 3000 | Static control shell                      |

## 3. Data Science Team — Agents (Phase 2)

| Agent        | Role                                                                 |
|--------------|----------------------------------------------------------------------|
| data_loader  | Load CSV / Parquet / Excel / JSON                                    |
| cleaner      | Drop empty cols/rows, impute nulls, strip strings, remove duplicates |
| eda          | Describe, missingness, correlations, value counts, cardinality       |
| visualizer   | Chart specs: histogram, bar, correlation heatmap (Plotly-ready)      |

**Default pipeline:** `data_loader → cleaner → eda → visualizer`

### API

| Method | Path                         | Description              |
|--------|------------------------------|--------------------------|
| GET    | `/health`                    | Health                   |
| GET    | `/v1/agents`                 | List agents              |
| POST   | `/v1/pipelines`              | Create pipeline          |
| GET    | `/v1/pipelines`              | List pipelines           |
| GET    | `/v1/pipelines/{id}`         | Get status + results     |
| POST   | `/v1/pipelines/{id}/run`     | Run (file or path)       |

## 4. Design Principles

1. Service isolation
2. Gateway as single LLM entrypoint
3. Ownership & security first
4. Observable pipelines
5. Extensible agent registry

## 5. Roadmap

| Phase | Deliverable                                   | Status  |
|-------|-----------------------------------------------|---------|
| 0     | Architecture docs                             | ✅ Done |
| 1     | Skeleton + Supervisor + Data Loader           | ✅ Done |
| 2     | Cleaner + EDA + Visualizer                    | ✅ Done |
| 3     | Feature engineering + basic modeling          | Next    |
| 4     | Code generation + reproducible scripts        | Planned |
| 5     | Auth reuse + persistent storage               | Planned |
| 6     | Web UI pipeline viewer                        | Planned |

## 6. References

- Inspiration: https://github.com/business-science/ai-data-science-team
- `docs/DATA_SCIENCE_TEAM.md`
