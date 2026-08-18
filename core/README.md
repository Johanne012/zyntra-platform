# NEXUS / ZYNTRA Core

This directory is the foundation for the unified intelligent command center.

## Mission

Turn the existing ZYNTRA platform into a reusable operating layer for multiple projects instead of a single application.

## Build order

1. Project registry and Project DNA
2. Task engine and event log
3. Persistent project memory
4. Diagnostics and health checks
5. Agent registry/runtime
6. Safe self-healing loop
7. Deployment readiness and rollback
8. Integrations and multi-project orchestration

## Safety model

Automatic changes are disabled by default. A future self-healing agent must validate changes, run tests, and support rollback before deployment.

## Existing platform

The current platform already contains a multi-provider gateway, agent service, web shell, usage/cost statistics, key management, notifications and run history. The Core layer will orchestrate these capabilities rather than replace them.
