# ZYNTRA Data Science Team

Supervisor-led multi-agent Data Science service.

## Quick start (local)

```bash
cd services/data-science-team
uv sync --extra dev
uv run uvicorn app.main:app --reload --port 8082
```

Health: http://localhost:8082/health

## Integration

This service is part of the ZYNTRA Platform monorepo.
See `docs/ARCHITECTURE.md` and `docs/DATA_SCIENCE_TEAM.md`.
