# Shared contracts — ZYNTRA Platform

## Gateway

### `GET /health`

Includes `balance_strategy` and per-provider `in_cooldown`.

### `GET /v1/stats`

In-memory usage: requests, tokens, `cost_usd`, cooldowns (resets on restart).

### `POST /v1/chat/completions`

OpenAI-compatible. Response may include:

```json
{ "zyntra": { "provider": "deepseek", "model": "deepseek-chat", "cost_usd": 0.0001 } }
```

Env: `GATEWAY_BALANCE_STRATEGY=priority|round_robin|random|weighted`

## Agents

### Auth

`Authorization: Bearer <api_key>`

### Keys

- `GET /v1/keys` — list prefixes only
- `POST /v1/keys` `{ "name" }` — returns raw key **once**
- `DELETE /v1/keys/{id}` — owner only

### Agents / runs / workflows

Unchanged ownership rules: foreign resources → **404**.

### Notifications

- `GET /v1/notifications`
- `POST /v1/notifications/{id}/read`

Created on register and after each agent run.
