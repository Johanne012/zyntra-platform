# Migration map — old repos → zyntra-platform

Gradual ports **without breaking** the monorepo layout. Dashboard UI is deferred.

## From `free-claude-gateway`

| Feature | Status in ZYNTRA |
|---------|------------------|
| Multi-provider OpenAI chat | ✅ `services/gateway` |
| Fallback chain | ✅ |
| Balance strategies (priority / rr / random / weighted) | ✅ `GATEWAY_BALANCE_STRATEGY` |
| Stats + rate-limit cooldown | ✅ `GET /v1/stats` |
| Cost estimate per request | ✅ `zyntra.cost_usd` + stats |
| Groq provider | ✅ |
| DeepSeek / OpenRouter / NIM / Kimi / Ollama | ✅ |
| Anthropic `/v1/messages` surface | ⏳ later |
| Per-key USD budgets in SQLite | ⏳ later (agents side) |
| Admin HTML dashboard | ❌ deferred (no UI phase) |
| Tool-calling passthrough | ⏳ later |

## From `Repository-name-my-ai-platform`

| Feature | Status |
|---------|--------|
| Hashed API keys + prefix | ✅ |
| Ownership checks (IDOR-safe) | ✅ |
| Agents CRUD + runs via gateway | ✅ |
| Workflows persist | ✅ |
| Extra keys create/list/revoke | ✅ |
| Notifications inbox | ✅ |
| Stripe / Manus coupling | ❌ not ported (by design) |
| React dashboard | ❌ deferred |

## From `zyntra-flowbrief`

| Feature | Status |
|---------|--------|
| Clear static landing | ✅ `apps/web` |
| Vercel rewrite safety | N/A (not Vercel-hosted here) |

## From `crypto-portfolio`

Not in scope for the AI platform core. Keep separate.

## Public patterns adopted

- OpenAI-compatible `/v1/chat/completions`
- Provider cooldown after HTTP 429
- SHA-256 API keys at rest
- Lifespan-based FastAPI startup

## How to extend next (still no UI)

1. Anthropic-compatible `/v1/messages` adapter in gateway
2. Persistent request log table (gateway) optional
3. Per-user daily request caps on agents
4. Tool-call passthrough when upstream supports it
