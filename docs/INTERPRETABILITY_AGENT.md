# Interpretability Agent — Design

## Goal
After modeling, explain **why** the model predicts what it predicts — globally and locally — in a form the rest of the ZYNTRA pipeline can return as JSON.

## Scope (Phase 3)

| Capability | Method | Output |
|------------|--------|--------|
| Global feature ranking | Permutation importance (sklearn) | ordered list of features + scores |
| Global attribution | SHAP summary (when available) | mean \|SHAP\| per feature |
| Local explanation | SHAP values for sample(s) | per-feature contribution |
| Dependence (optional) | Partial dependence for top-2 features | curve points |

## Design decisions

1. **Model-agnostic first** — works with any sklearn-compatible estimator stored in pipeline context.
2. **Graceful degradation** — if `shap` is not installed or model unsupported, fall back to permutation importance only.
3. **No heavy deep-learning XAI** in Phase 3 (Grad-CAM etc. later).
4. **JSON-safe** — never return raw matplotlib figures; only data for the web UI to plot.
5. **Runs only after `modeler`** — needs `context["model"]` and `context["dataframe"]` (+ target column).

## Context contract

**Input (from previous agents):**
```text
dataframe: pd.DataFrame          # features (+ optional target still present)
model: fitted estimator
feature_columns: list[str]
target_column: str | None
X_train, y_train, X_test, y_test  # optional splits from modeler
```

**Output (public JSON):**
```json
{
  "status": "ok",
  "agent": "interpretability",
  "global_importance": [{"feature": "age", "score": 0.12}, ...],
  "method": "permutation" | "shap",
  "local_explanations": [],
  "notes": []
}
```

## Pipeline position

```text
data_loader → cleaner → eda → visualizer → feature_engineer → modeler → interpretability
```

Default Phase 3 steps include all of the above.
