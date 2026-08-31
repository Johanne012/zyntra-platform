"""Feature Engineering Agent — simple, safe transforms for tabular data."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.agents.base import BaseAgent


class FeatureEngineerAgent(BaseAgent):
    name = "feature_engineer"
    description = "Create basic features: one-hot encode categoricals, scale numerics, drop high-cardinality IDs"

    async def run(self, context: dict[str, Any], instruction: str = "") -> dict[str, Any]:
        df: pd.DataFrame | None = context.get("dataframe")
        if df is None:
            return {
                "status": "error",
                "agent": self.name,
                "error": "No dataframe in context. Run data_loader first.",
            }

        actions: list[str] = []
        original_cols = list(df.columns)
        work = df.copy()

        # Drop columns that look like pure IDs (high cardinality, object)
        drop_ids: list[str] = []
        for col in work.select_dtypes(include=["object", "string"]).columns:
            nunique = work[col].nunique(dropna=True)
            if nunique > max(50, int(0.5 * len(work))):
                drop_ids.append(col)
        if drop_ids:
            work = work.drop(columns=drop_ids)
            actions.append(f"Dropped high-cardinality ID-like columns: {drop_ids}")

        # One-hot encode remaining low/medium cardinality categoricals
        cat_cols = list(work.select_dtypes(include=["object", "string", "category"]).columns)
        encoded_cols: list[str] = []
        if cat_cols:
            # Limit to avoid explosion
            safe_cats = [c for c in cat_cols if work[c].nunique(dropna=True) <= 20]
            skipped = [c for c in cat_cols if c not in safe_cats]
            if skipped:
                work = work.drop(columns=skipped)
                actions.append(f"Dropped high-cardinality categoricals (>{20} levels): {skipped}")
            if safe_cats:
                dummies = pd.get_dummies(work[safe_cats], prefix=safe_cats, dummy_na=False)
                work = work.drop(columns=safe_cats)
                work = pd.concat([work, dummies], axis=1)
                encoded_cols = list(dummies.columns)
                actions.append(f"One-hot encoded: {safe_cats} → {len(encoded_cols)} columns")

        # Standardize numeric columns (z-score), keep as float
        num_cols = list(work.select_dtypes(include="number").columns)
        scaled: list[str] = []
        for col in num_cols:
            std = work[col].std()
            if std and std > 0:
                work[col] = (work[col] - work[col].mean()) / std
                scaled.append(col)
        if scaled:
            actions.append(f"Z-score scaled {len(scaled)} numeric columns")

        if not actions:
            actions.append("No feature engineering applied")

        feature_columns = list(work.columns)

        return {
            "status": "ok",
            "agent": self.name,
            "original_columns": original_cols,
            "feature_columns": feature_columns,
            "n_features": len(feature_columns),
            "actions": actions,
            "encoded_columns": encoded_cols,
            "_dataframe": work,
            "_feature_columns": feature_columns,
        }
