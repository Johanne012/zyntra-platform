# Contributing to ZYNTRA Platform

## Workflow

1. Branch from `main`: `feat/...`, `fix/...`, or `improve/...`.
2. Keep changes scoped to one service when possible.
3. Run local checks before PR:
   - Gateway: `cd services/gateway && uv run ruff check . && uv run pytest -q`
   - Agents: `cd services/agents && uv run ruff check . && uv run pytest -q`
4. Open a PR against `main`. CI must pass.

## Code style

- Python 3.11+
- Ruff for lint + format
- Type hints on public APIs
- Async FastAPI endpoints

## Contracts

Shared request/response shapes live under `packages/shared`. Prefer updating the contract first when changing APIs.
