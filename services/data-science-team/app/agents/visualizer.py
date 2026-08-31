"""Visualizer Agent — generate simple chart specs (JSON) for frontend rendering."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.agents.base import BaseAgent


class VisualizerAgent(BaseAgent):
    name = "visualizer"
    description = "Produce chart specifications (histograms, bar, correlation heatmap)"

    async def run(self, context: dict[str, Any], instruction: str = "") -> dict[str, Any]:
        df: pd.DataFrame | None = context.get("dataframe")
        if df is None:
            return {
                "status": "error",
                "agent": self.name,
                "error": "No dataframe in context. Run data_loader first.",
            }

        charts: list[dict[str, Any]] = []

        numeric = df.select_dtypes(include="number")
        categorical = df.select_dtypes(exclude="number")

        # Histograms for up to 6 numeric columns
        for col in list(numeric.columns)[:6]:
            series = numeric[col].dropna()
            if series.empty:
                continue
            # Simple binning
            counts, bin_edges = pd.cut(series, bins=min(20, max(5, len(series) // 5)), retbins=True, include_lowest=True)
            hist = counts.value_counts().sort_index()
            charts.append(
                {
                    "type": "histogram",
                    "title": f"Distribution of {col}",
                    "x_label": col,
                    "y_label": "count",
                    "labels": [str(i) for i in hist.index.astype(str)],
                    "values": [int(v) for v in hist.values],
                }
            )

        # Bar charts for up to 4 categorical columns
        for col in list(categorical.columns)[:4]:
            vc = df[col].value_counts(dropna=False).head(15)
            charts.append(
                {
                    "type": "bar",
                    "title": f"Counts of {col}",
                    "x_label": col,
                    "y_label": "count",
                    "labels": [str(k) for k in vc.index],
                    "values": [int(v) for v in vc.values],
                }
            )

        # Correlation heatmap data
        if numeric.shape[1] >= 2:
            corr = numeric.corr(numeric_only=True).round(3)
            charts.append(
                {
                    "type": "heatmap",
                    "title": "Correlation matrix",
                    "labels": list(corr.columns),
                    "matrix": corr.values.tolist(),
                }
            )

        return {
            "status": "ok",
            "agent": self.name,
            "chart_count": len(charts),
            "charts": charts,
            "_dataframe": df,
        }
