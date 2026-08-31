# Data Science Team Service — Integration Plan

## Why this service?

We are embedding a specialized **multi-agent Data Science team** into ZYNTRA so users can:

- Upload datasets
- Run automated cleaning, EDA, feature engineering and modeling
- Get reproducible Python pipelines
- Keep everything under the same authentication & gateway as the rest of the platform

## Source

Based on the excellent open-source project:  
**https://github.com/business-science/ai-data-science-team** (MIT)

We will adapt it to:

1. Use ZYNTRA Gateway for all LLM calls
2. Follow the same service layout & security model
3. Expose a clean FastAPI surface
4. Be fully testable via GitHub Actions

## Service Layout (target)

```
services/data-science-team/
├── Dockerfile
├── pyproject.toml
├── README.md
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── security.py
│   ├── gateway_client.py
│   ├── supervisor.py
│   ├── pipeline.py
│   └── agents/
│       ├── __init__.py
│       ├── base.py
│       ├── data_loader.py
│       ├── cleaner.py
│       ├── eda.py
│       ├── visualizer.py
│       ├── feature_engineer.py
│       └── modeler.py
└── tests/
    ├── test_health.py
    └── test_supervisor.py
```

## API Surface (Phase 1)

| Method | Path                        | Description                    |
|--------|-----------------------------|--------------------------------|
| GET    | `/health`                   | Health check                   |
| POST   | `/v1/datasets`              | Upload / register dataset      |
| GET    | `/v1/datasets`              | List datasets                  |
| POST   | `/v1/pipelines`             | Start a new DS pipeline        |
| GET    | `/v1/pipelines/{id}`        | Get pipeline status + results  |
| POST   | `/v1/pipelines/{id}/steps`  | Run next step (or auto)        |

## Authentication

Same as Agents service: `Authorization: Bearer <zyntra-api-key>`

## Next Immediate Steps

1. Create service skeleton + health endpoint
2. Wire into `docker-compose.yml`
3. Extend GitHub Actions CI
4. Implement Supervisor + Data Loader agent
