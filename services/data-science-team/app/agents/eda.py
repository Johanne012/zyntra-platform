"""EDA Agent — exploratory data analysis summary."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.agents.base import BaseAgent


class EDAAgent(BaseAgent):
    name = "eda"
    description = "Exploratory data analysis: describe, missingness, correlations, value counts"

    async def run(self, context: dict[str, Any], instruction: str = "") -> dict[str, Any]:
        df: pd.DataFrame | None = context.get("dataframe")
        if df is None:
            return {
                "status": "error",
                "agent": self.name,
                "error": "No dataframe in context. Run data_loader first.",
            }

        numeric = df.select_dtypes(include="number")
        categorical = df.select_dtypes(include=["object", "string", "category"])

        # Describe numeric
        describe: dict[str, Any] = {}
        if not numeric.empty:
            desc = numeric.describe().round(4)
            describe = desc.to_dict()

        # Missingness
        missing = {
            col: {
                "count": int(df[col].isna().sum()),
                "pct": round(float(df[col].isna().mean() * 100), 2),
            }
            for col in df.columns
            if df[col].isna().any()
        }

        # Correlations (numeric only, if >= 2 cols)
        correlations: dict[str, Any] = {}
        if numeric.shape[1] >= 2:
            corr = numeric.corr(numeric_only=True).round(4)
            correlations = corr.to_dict()

        # Top value counts for categorical (max 5 cols, top 10 values each)
        value_counts: dict[str, Any] = {}
        for col in list(categorical.columns)[:5]:
            vc = df[col].value_counts(dropna=False).head(10)
            value_counts[col] = {str(k): int(v) for k, v in vc.items()}

        # Cardinality
        cardinality = {col: int(df[col].nunique(dropna=True)) for col in df.columns}

        return {
            "status": "ok",
            "agent": self.name,
            "shape": list(df.shape),
            "dtypes": {c: str(t) for c, t in df.dtypes.items()},
            "describe": describe,
            "missing": missing,
            "correlations": correlations,
            "value_counts": value_counts,
            "cardinality": cardinality,
            "_dataframe": df,  # pass through unchanged
        }
