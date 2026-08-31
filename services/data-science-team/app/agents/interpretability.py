"""Interpretability Agent — permutation importance (+ optional SHAP)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance

from app.agents.base import BaseAgent


class InterpretabilityAgent(BaseAgent):
    name = "interpretability"
    description = "Explain model: permutation importance and optional SHAP summary"

    async def run(self, context: dict[str, Any], instruction: str = "") -> dict[str, Any]:
        model = context.get("model") or context.get("_model")
        X_test = context.get("X_test") or context.get("_X_test")
        y_test = context.get("y_test") or context.get("_y_test")
        feature_columns = context.get("feature_columns") or context.get("_feature_columns")

        # Fallback: rebuild from dataframe if splits missing
        if model is None:
            return {
                "status": "error",
                "agent": self.name,
                "error": "No fitted model in context. Run modeler first.",
            }

        if X_test is None or y_test is None:
            df = context.get("dataframe")
            target = context.get("target_column") or context.get("_target_column")
            if df is None or not target or target not in df.columns:
                return {
                    "status": "error",
                    "agent": self.name,
                    "error": "Missing X_test/y_test and cannot rebuild from dataframe.",
                }
            cols = feature_columns or [c for c in df.columns if c != target]
            X_test = df[cols].select_dtypes(include="number")
            y_test = df[target]
            feature_columns = list(X_test.columns)

        notes: list[str] = []
        method = "permutation"

        # Permutation importance (always available)
        try:
            r = permutation_importance(
                model,
                X_test,
                y_test,
                n_repeats=5,
                random_state=42,
                n_jobs=-1,
            )
            global_importance = sorted(
                [
                    {
                        "feature": str(f),
                        "score": float(s),
                        "std": float(std),
                    }
                    for f, s, std in zip(
                        feature_columns or X_test.columns,
                        r.importances_mean,
                        r.importances_std,
                    )
                ],
                key=lambda x: x["score"],
                reverse=True,
            )
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "error",
                "agent": self.name,
                "error": f"Permutation importance failed: {exc}",
            }

        # Optional SHAP (tree models)
        shap_summary: list[dict[str, Any]] = []
        local_explanations: list[dict[str, Any]] = []
        try:
            import shap  # type: ignore

            explainer = shap.TreeExplainer(model)
            # Limit rows for speed
            sample = X_test
            if hasattr(sample, "iloc") and len(sample) > 100:
                sample = sample.iloc[:100]
            shap_values = explainer.shap_values(sample)

            # Binary/multiclass: shap_values may be list
            if isinstance(shap_values, list):
                # use class 1 if binary else mean abs across classes
                sv = shap_values[1] if len(shap_values) == 2 else np.mean(
                    np.abs(shap_values), axis=0
                )
            else:
                sv = shap_values

            mean_abs = np.mean(np.abs(sv), axis=0)
            shap_summary = sorted(
                [
                    {"feature": str(f), "mean_abs_shap": float(v)}
                    for f, v in zip(feature_columns or sample.columns, mean_abs)
                ],
                key=lambda x: x["mean_abs_shap"],
                reverse=True,
            )
            method = "permutation+shap"

            # One local explanation (first row)
            row0 = {str(f): float(v) for f, v in zip(feature_columns or sample.columns, sv[0])}
            local_explanations.append(
                {
                    "index": 0,
                    "shap_values": row0,
                    "base_value": float(
                        explainer.expected_value[1]
                        if isinstance(explainer.expected_value, (list, np.ndarray))
                        and len(np.atleast_1d(explainer.expected_value)) > 1
                        else float(np.atleast_1d(explainer.expected_value)[0])
                    ),
                }
            )
            notes.append("SHAP TreeExplainer succeeded on sample (up to 100 rows).")
        except Exception as exc:  # noqa: BLE001
            notes.append(f"SHAP skipped: {exc}")

        return {
            "status": "ok",
            "agent": self.name,
            "method": method,
            "global_importance": global_importance[:30],
            "shap_summary": shap_summary[:30],
            "local_explanations": local_explanations,
            "notes": notes,
            # pass through model artifacts
            "_model": model,
            "_dataframe": context.get("dataframe"),
        }
