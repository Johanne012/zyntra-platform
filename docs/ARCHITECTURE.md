# ZYNTRA Platform — System Architecture

> Last updated: 2026-08-31  
> Status: v0.6 — Data Science Team Phase 4 (code generation)

## Data Science Team agents

| Agent | Role |
|--------|------|
| data_loader | Load tabular files |
| cleaner | Impute / dedupe / strip |
| eda | Statistical summary |
| visualizer | Chart JSON specs |
| feature_engineer | Encode + scale |
| modeler | RandomForest baseline |
| interpretability | Permutation (+ SHAP optional) |
| code_generator | Reproducible Python script |

Default order: all eight steps.

### Extra endpoint

`GET /v1/pipelines/{id}/script` → plain-text generated `.py`

`POST .../run` accepts optional form field `target_column`.

See also: `docs/CODE_GENERATOR.md`, `docs/INTERPRETABILITY_AGENT.md`.

## Roadmap

| Phase | Status |
|-------|--------|
| 0–3 | ✅ |
| 4 Code generation | ✅ |
| 5 Auth + persistence | Planned |
| 6 Web pipeline viewer | Planned |
