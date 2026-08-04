# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| main    | Yes       |

## Reporting a vulnerability

Open a private security advisory on GitHub or email the maintainer. Do not open a public issue for active exploits.

## Design principles in this monorepo

1. **API keys** — generated with `secrets.token_hex(32)`, stored as SHA-256 hashes; only a short prefix is stored for UI display. The raw key is returned once at creation.
2. **Ownership** — every agent, run, and notification mutation must verify `resource.owner_id == current_user.id`.
3. **Secrets** — provider keys and `AGENTS_SECRET_KEY` live in environment variables only.
4. **Streaming** — gateway uses short-lived DB/log sessions; never hold a request-scoped session across an entire stream.
5. **Headers** — agents service sets basic security headers (X-Content-Type-Options, etc.).

## What not to do

- Do not put real API keys in client-side JavaScript for production.
- Do not log full prompt/response bodies in production by default.
- Do not disable ownership checks to "make demos easier".
