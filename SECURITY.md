# Security Policy

## Reporting

Open a private GitHub security advisory. Do not file public issues for active exploits.

## Gateway

See [docs/SECURITY_GATEWAY.md](docs/SECURITY_GATEWAY.md).

- Optional `GATEWAY_API_KEY` (required in production)
- Per-IP rate limiting
- Restricted CORS origins
- Security response headers
- `/health` public; `/v1/*` authenticated when key is set

## Agents

- API keys: `secrets.token_hex` + SHA-256 at rest; prefix for display only
- Ownership checks on agents, runs, keys, notifications, workflows
- Security headers middleware
- Internal calls to gateway send `GATEWAY_API_KEY_INTERNAL` when set

## Repository hygiene

- Never commit `.env`
- Protect `main`: [docs/BRANCH_PROTECTION.md](docs/BRANCH_PROTECTION.md)
- `CODEOWNERS` → @Johanne012
