"""Data Cleaner Agent — basic cleaning and imputation."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.agents.base import BaseAgent


class CleanerAgent(BaseAgent):
    name = "cleaner"
    description = "Clean data: drop empty columns/rows, impute missing values, strip strings"

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

        # 1. Drop fully empty columns
        empty_cols = [c for c in df.columns if df[c].isna().all()]
        if empty_cols:
            df = df.drop(columns=empty_cols)
            actions.append(f"Dropped empty columns: {empty_cols}")

        # 2. Drop fully empty rows
        before_rows = len(df)
        df = df.dropna(how="all")
        dropped_rows = before_rows - len(df)
        if dropped_rows:
            actions.append(f"Dropped {dropped_rows} fully empty rows")

        # 3. Strip string columns
        str_cols = df.select_dtypes(include=["object", "string"]).columns
        for col in str_cols:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})
        if len(str_cols):
            actions.append(f"Stripped whitespace on {len(str_cols)} string columns")

        # 4. Impute numeric columns with median
        num_cols = df.select_dtypes(include="number").columns
        imputed_num: dict[str, float] = {}
        for col in num_cols:
            null_count = int(df[col].isna().sum())
            if null_count > 0:
                median = float(df[col].median())
                df[col] = df[col].fillna(median)
                imputed_num[col] = median
        if imputed_num:
            actions.append(f"Imputed numeric nulls with median: {imputed_num}")

        # 5. Impute categorical with mode
        cat_cols = df.select_dtypes(include=["object", "string", "category"]).columns
        imputed_cat: dict[str, str] = {}
        for col in cat_cols:
            null_count = int(df[col].isna().sum())
            if null_count > 0:
                mode = df[col].mode(dropna=True)
                fill_value = str(mode.iloc[0]) if len(mode) else "unknown"
                df[col] = df[col].fillna(fill_value)
                imputed_cat[col] = fill_value
        if imputed_cat:
            actions.append(f"Imputed categorical nulls with mode: {imputed_cat}")

        # 6. Drop duplicate rows
        before_dup = len(df)
        df = df.drop_duplicates()
        dup_removed = before_dup - len(df)
        if dup_removed:
            actions.append(f"Removed {dup_removed} duplicate rows")

        if not actions:
            actions.append("No cleaning actions needed")

        return {
            "status": "ok",
            "agent": self.name,
            "original_shape": original_shape,
            "final_shape": list(df.shape),
            "actions": actions,
            "remaining_nulls": df.isnull().sum().to_dict(),
            "_dataframe": df,
        }
