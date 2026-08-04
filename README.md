# ZYNTRA Platform

Unified AI platform: **multi-provider LLM gateway**, **agent runtime**, and **web shell** — one coherent monorepo.

[![CI](https://github.com/Johanne012/zyntra-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/Johanne012/zyntra-platform/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Architecture

```
apps/web  →  services/agents  →  services/gateway  →  providers
```

## Quick start

```bash
git clone https://github.com/Johanne012/zyntra-platform.git
cd zyntra-platform
cp .env.example .env
# set at least one provider key
docker compose up --build
```

| Service | URL |
|---------|-----|
| Gateway | http://localhost:8080 |
| Agents | http://localhost:8081 |
| Web | http://localhost:3000 |
| Stats | http://localhost:8080/v1/stats |

## What was ported (v0.2)

From your strongest repos + common public patterns — **without a control-panel UI**:

- Balance strategies + cooldown after 429
- Usage / cost stats
- Groq + existing providers
- Extra API keys + revoke
- Notifications + run history list

See [docs/MIGRATION.md](docs/MIGRATION.md).

## Layout

```
apps/web/
services/gateway/   # OpenAI-compatible proxy
services/agents/    # keys, agents, workflows, notifications
packages/shared/    # contracts
```

## Security

API keys hashed (SHA-256); ownership on every mutate/read of agents, runs, keys, notifications. Details: [SECURITY.md](SECURITY.md).

## License

MIT
