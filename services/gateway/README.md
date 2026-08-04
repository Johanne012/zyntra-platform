# ZYNTRA Gateway

OpenAI-compatible multi-provider proxy with ordered fallback and streaming.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness |
| GET | `/v1/models` | Listed models |
| POST | `/v1/chat/completions` | Chat (stream supported) |

## Providers

Configured via env (see root `.env.example`). Default order tries the first available key.
