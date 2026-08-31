# ZYNTRA Platform — System Architecture

> Last updated: 2026-08-31  
> Status: Living document (v0.5 — Data Science Team Phase 3)

## 1. Overview

```
apps/web → services/agents → services/gateway → providers
                ↘
         services/data-science-team  (port 8082)
```

## 2. Data Science Team — Full agent chain

| # | Agent | Role |
|---|--------|------|
| 1 | data_loader | Load CSV / Parquet / Excel / JSON |
| 2 | cleaner | Impute, strip, drop empty/duplicates |
| 3 | eda | Describe, missing, correlations |
| 4 | visualizer | Histogram / bar / heatmap specs |
| 5 | feature_engineer | One-hot, scale, drop high-cardinality |
| 6 | modeler | RandomForest baseline + metrics |
| 7 | interpretability | Permutation importance (+ SHAP if available) |

**Default pipeline:** all seven steps in order.

Design notes for interpretability: see `docs/INTERPRETABILITY_AGENT.md`.

## 3. Context flow between agents

```
dataframe → (cleaner/eda/viz) → feature matrix
         → modeler fits model + train/test splits
         → interpretability reads model + X_test/y_test
```

Internal keys (`_model`, `_X_test`, …) are stripped from public API responses.

## 4. API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health |
| GET | `/v1/agents` | List agents |
| POST | `/v1/pipelines` | Create (optional custom `steps`) |
| GET | `/v1/pipelines` | List |
| GET | `/v1/pipelines/{id}` | Status + results |
| POST | `/v1/pipelines/{id}/run` | Upload file or `path` form field |

Optional form/instruction for target: modeler accepts `target_column` in context or `target=colname` in instruction (future API extension).

## 5. Dependencies

- Core: pandas, scikit-learn, fastapi
- Optional: `shap` via `pip install zyntra-data-science-team[explain]`

## 6. Roadmap

| Phase | Status |
|-------|--------|
| 0 Docs | ✅ |
| 1 Skeleton + loader | ✅ |
| 2 Cleaner + EDA + Viz | ✅ |
| 3 Feature eng + model + interpretability | ✅ |
| 4 Code generation / reproducible scripts | Planned |
| 5 Auth + persistent storage | Planned |
| 6 Web pipeline viewer | Planned |
