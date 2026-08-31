"""Data Cleaner Agent — basic cleaning & imputation."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.agents.base import BaseAgent


class CleanerAgent(BaseAgent):
    name = "cleaner"
    description = "Clean data: drop empty columns, handle nulls, strip strings, drop duplicates"

    async def run(self, context: dict[str, Any], instruction: str = "") -> dict[str, Any]:
        df: pd.DataFrame | None = context.get("dataframe")
        if df is None:
            return {
                "status": "error",
                "agent": self.name,
                "error": "No dataframe in context. Run data_loader first.",
            }

        original_shape = list(df.shape)
        actions: list[str] = []

        # Drop columns that are entirely null
        all_null_cols = [c for c in df.columns if df[c].isna().all()]
        if all_null_cols:
            df = df.drop(columns=all_null_cols)
            actions.append(f"Dropped entirely-null columns: {all_null_cols}")

        # Strip whitespace from string columns
        str_cols = df.select_dtypes(include=["object", "string"]).columns
        for col in str_cols:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})
        if len(str_cols):
            actions.append(f"Stripped whitespace on {len(str_cols)} string columns")

        # Drop exact duplicate rows
        before_dup = len(df)
        df = df.drop_duplicates()
        dropped_dups = before_dup - len(df)
        if dropped_dups:
            actions.append(f"Dropped {dropped_dups} duplicate rows")

        # Simple numeric imputation (median) for columns with < 30% nulls
        numeric_cols = df.select_dtypes(include="number").columns
        imputed: list[str] = []
        for col in numeric_cols:
            null_ratio = df[col].isna().mean()
            if 0 < null_ratio < 0.3:
                median = df[col].median()
                df[col] = df[col].fillna(median)
                imputed.append(col)
        if imputed:
            actions.append(f"Median-imputed numeric columns: {imputed}")

        # Fill remaining object nulls with mode (if mode exists)
        for col in str_cols:
            if col not in df.columns:
                continue
            if df[col].isna().any():
                mode = df[col].mode()
                if len(mode):
                    df[col] = df[col].fillna(mode.iloc[0])
                    actions.append(f"Mode-filled string column: {col}")

        return {
            "status": "ok",
            "agent": self.name,
            "original_shape": original_shape,
            "cleaned_shape": list(df.shape),
            "actions": actions,
            "null_counts_after": df.isnull().sum().to_dict(),
            "_dataframe": df,
        }
