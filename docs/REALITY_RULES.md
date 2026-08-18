# Reality Rules

These rules govern NEXUS development.

1. A UI element must map to a real action or be labelled as planned.
2. Operational status requires a real health check.
3. External integrations are unavailable until credentials/configuration are verified.
4. Never commit secrets, tokens, or private keys.
5. Prefer fixing a defect over hiding it.
6. If a component is irreparably incompatible, replace it only after preserving required behavior and tests.
7. Every destructive change needs a rollback path.
8. A deployment is successful only after post-deploy smoke tests pass.
9. Tests must distinguish configuration failures from application failures.
10. Documentation must match the actual implementation.
