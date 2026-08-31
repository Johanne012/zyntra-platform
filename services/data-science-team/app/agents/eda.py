"""EDA Agent — exploratory data analysis summary."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.agents.base import BaseAgent


class EDAAgent(BaseAgent):
    name = "eda"
    description = "Exploratory data analysis: describe, missingness, correlations"

    async def run(self, context: dict[str, Any], instruction: str = "") -> dict[str, Any]:
        df: pd.DataFrame | None = context.get("dataframe")
        if df is None:
            return {
                "status": "error",
                "agent": self.name,
                "error": "No dataframe in context. Run data_loader first.",
            }

        numeric = df.select_dtypes(include="number")
        categorical = df.select_dtypes(exclude="number")

        describe = {}
        if not numeric.empty:
            describe = numeric.describe().round(4).to_dict()

        missing = {
            col: {
                "count": int(df[col].isna().sum()),
                "ratio": round(float(df[col].isna().mean()), 4),
            }
            for col in df.columns
            if df[col].isna().any()
        }

        correlations: dict[str, Any] = {}
        if numeric.shape[1] >= 2:
            corr = numeric.corr(numeric_only=True).round(4)
            correlations = corr.to_dict()

        value_counts: dict[str, Any] = {}
        for col in categorical.columns[:10]:  # limit
            vc = df[col].value_counts(dropna=False).head(10)
            value_counts[col] = {str(k): int(v) for k, v in vc.items()}

        return {
            "status": "ok",
            "agent": self.name,
            "shape": list(df.shape),
            "numeric_columns": list(numeric.columns),
            "categorical_columns": list(categorical.columns),
            "describe": describe,
            "missing": missing,
            "correlations": correlations,
            "top_value_counts": value_counts,
            "_dataframe": df,
        }
