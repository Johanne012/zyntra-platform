# Shared contracts — ZYNTRA Platform

These shapes keep **gateway**, **agents**, and **web** aligned.

## Gateway

### `GET /health`

```json
{
  "status": "ok",
  "service": "zyntra-gateway",
  "providers": [{ "id": "deepseek", "available": true }]
}
```

### `POST /v1/chat/completions` (OpenAI-compatible)

Request:

```json
{
  "model": "gpt-4o-mini",
  "messages": [{ "role": "user", "content": "Hello" }],
  "stream": false,
  "provider": null
}
```

Response includes optional:

```json
{ "zyntra": { "provider": "deepseek", "model": "deepseek-chat" } }
```

## Agents

### `POST /v1/register`

```json
{ "email": "you@example.com" }
```

→ `{ "user_id", "email", "api_key", "key_prefix" }`  
`api_key` is shown **once**.

### Auth

`Authorization: Bearer <api_key>`

### Agents CRUD

- `POST /v1/agents` `{ name, system_prompt?, model? }`
- `GET /v1/agents`
- `GET|DELETE /v1/agents/{id}` — **404 if not owner**

### Runs

- `POST /v1/agents/{id}/runs` `{ input_text }` → calls **gateway** internally
- `GET /v1/runs/{id}` — owner only

### Workflows

- `POST /v1/workflows` `{ name, definition_json? }`
- `GET /v1/workflows` — scoped to user
