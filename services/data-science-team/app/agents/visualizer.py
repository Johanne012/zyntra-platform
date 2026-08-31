"""Visualizer Agent — generate simple chart specs (Plotly-ready JSON)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.agents.base import BaseAgent


class VisualizerAgent(BaseAgent):
    name = "visualizer"
    description = "Generate chart specifications (histogram, bar, correlation heatmap)"

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
        categorical = df.select_dtypes(include=["object", "string", "category"])

        # Histograms for up to 4 numeric columns
        for col in list(numeric.columns)[:4]:
            series = df[col].dropna()
            if series.empty:
                continue
            charts.append(
                {
                    "type": "histogram",
                    "title": f"Distribution of {col}",
                    "x": col,
                    "data": {
                        "x": series.tolist()[:5000],  # cap for payload size
                    },
                    "layout": {"xaxis_title": col, "yaxis_title": "Count"},
                }
            )

        # Bar charts for up to 3 categorical columns (top 15 values)
        for col in list(categorical.columns)[:3]:
            vc = df[col].value_counts(dropna=True).head(15)
            if vc.empty:
                continue
            charts.append(
                {
                    "type": "bar",
                    "title": f"Value counts: {col}",
                    "x": col,
                    "data": {
                        "x": [str(k) for k in vc.index.tolist()],
                        "y": vc.tolist(),
                    },
                    "layout": {"xaxis_title": col, "yaxis_title": "Count"},
                }
            )

        # Correlation heatmap if enough numeric cols
        if numeric.shape[1] >= 2:
            corr = numeric.corr(numeric_only=True).round(3)
            charts.append(
                {
                    "type": "heatmap",
                    "title": "Correlation matrix",
                    "data": {
                        "z": corr.values.tolist(),
                        "x": corr.columns.tolist(),
                        "y": corr.index.tolist(),
                    },
                    "layout": {"xaxis_title": "", "yaxis_title": ""},
                }
            )

        return {
            "status": "ok",
            "agent": self.name,
            "chart_count": len(charts),
            "charts": charts,
            "_dataframe": df,
        }
