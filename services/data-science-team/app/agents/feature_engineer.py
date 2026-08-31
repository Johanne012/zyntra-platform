"""Feature Engineering Agent — richer tabular transforms."""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

from app.agents.base import BaseAgent

# Name patterns that usually mean identifier columns
_ID_PATTERN = re.compile(
    r"(^id$|_id$|^uuid$|^guid$|^pk$|customer_id|user_id|account_id)",
    re.IGNORECASE,
)


class FeatureEngineerAgent(BaseAgent):
    name = "feature_engineer"
    description = (
        "Feature engineering: protect target, drop IDs, datetime parts, "
        "one-hot / frequency encode, log1p skew, robust scale"
    )

    async def run(self, context: dict[str, Any], instruction: str = "") -> dict[str, Any]:
        df: pd.DataFrame | None = context.get("dataframe")
        if df is None:
            return {
                "status": "error",
                "agent": self.name,
                "error": "No dataframe in context. Run data_loader first.",
            }

        target_column = self._resolve_target(context, instruction, df)
        actions: list[str] = []
        original_cols = list(df.columns)
        work = df.copy()

        # Keep target aside so we never encode/scale it as a feature
        target_series: pd.Series | None = None
        if target_column and target_column in work.columns:
            target_series = work[target_column].copy()
            work = work.drop(columns=[target_column])
            actions.append(f"Protected target column from transforms: {target_column}")

        # --- Datetime extraction ---
        dt_cols = self._detect_datetime_columns(work)
        dt_created: list[str] = []
        for col in dt_cols:
            parsed = pd.to_datetime(work[col], errors="coerce", utc=False)
            work[f"{col}_year"] = parsed.dt.year
            work[f"{col}_month"] = parsed.dt.month
            work[f"{col}_day"] = parsed.dt.day
            work[f"{col}_dayofweek"] = parsed.dt.dayofweek
            work[f"{col}_hour"] = parsed.dt.hour
            work[f"{col}_is_weekend"] = (parsed.dt.dayofweek >= 5).astype("Int64")
            dt_created.extend(
                [
                    f"{col}_year",
                    f"{col}_month",
                    f"{col}_day",
                    f"{col}_dayofweek",
                    f"{col}_hour",
                    f"{col}_is_weekend",
                ]
            )
            work = work.drop(columns=[col])
        if dt_cols:
            actions.append(f"Extracted datetime parts from {dt_cols} → {len(dt_created)} columns")

        # --- Drop ID-like columns ---
        drop_ids: list[str] = []
        for col in list(work.columns):
            if col in dt_created:
                continue
            if _ID_PATTERN.search(str(col)):
                drop_ids.append(col)
                continue
            if work[col].dtype == object or str(work[col].dtype) == "string":
                nunique = work[col].nunique(dropna=True)
                if nunique > max(50, int(0.5 * len(work))):
                    drop_ids.append(col)
        drop_ids = list(dict.fromkeys(drop_ids))
        if drop_ids:
            work = work.drop(columns=[c for c in drop_ids if c in work.columns])
            actions.append(f"Dropped ID / high-cardinality columns: {drop_ids}")

        # --- Categorical encoding ---
        cat_cols = list(work.select_dtypes(include=["object", "string", "category"]).columns)
        encoded_cols: list[str] = []
        freq_cols: list[str] = []

        if cat_cols:
            low = [c for c in cat_cols if work[c].nunique(dropna=True) <= 20]
            mid = [c for c in cat_cols if 20 < work[c].nunique(dropna=True) <= 100]
            high = [c for c in cat_cols if work[c].nunique(dropna=True) > 100]

            if high:
                work = work.drop(columns=high)
                actions.append(f"Dropped very high-cardinality categoricals (>100): {high}")

            if mid:
                for col in mid:
                    freq = work[col].value_counts(dropna=False)
                    work[f"{col}_freq"] = work[col].map(freq).astype(float)
                    freq_cols.append(f"{col}_freq")
                work = work.drop(columns=mid)
                actions.append(f"Frequency-encoded: {mid}")

            if low:
                dummies = pd.get_dummies(work[low], prefix=low, dummy_na=False)
                work = work.drop(columns=low)
                work = pd.concat([work, dummies], axis=1)
                encoded_cols = list(dummies.columns)
                actions.append(f"One-hot encoded: {low} → {len(encoded_cols)} columns")

        # --- Numeric: log1p for positive skew, then robust scale ---
        num_cols = list(work.select_dtypes(include="number").columns)
        log_cols: list[str] = []
        scaled: list[str] = []

        for col in num_cols:
            s = work[col].astype(float)
            if s.notna().sum() < 3:
                continue

            # log1p only if strictly non-negative and skewed
            if (s.dropna() >= 0).all():
                skew = float(s.skew()) if s.notna().sum() > 2 else 0.0
                if abs(skew) > 1.0:
                    work[col] = np.log1p(s)
                    log_cols.append(col)
                    s = work[col]

            median = float(s.median())
            q1, q3 = float(s.quantile(0.25)), float(s.quantile(0.75))
            iqr = q3 - q1
            if iqr > 0:
                work[col] = (s - median) / iqr
                scaled.append(col)
            else:
                std = float(s.std())
                if std and std > 0:
                    work[col] = (s - float(s.mean())) / std
                    scaled.append(col)

        if log_cols:
            actions.append(f"log1p on skewed non-negative columns: {log_cols}")
        if scaled:
            actions.append(
                f"Robust-scaled (median/IQR, fallback z-score) {len(scaled)} numeric columns"
            )

        # Restore target at the end (untransformed)
        if target_series is not None and target_column:
            work[target_column] = target_series.values

        if not actions:
            actions.append("No feature engineering applied")

        feature_columns = [c for c in work.columns if c != target_column]

        return {
            "status": "ok",
            "agent": self.name,
            "original_columns": original_cols,
            "feature_columns": feature_columns,
            "n_features": len(feature_columns),
            "target_column": target_column,
            "actions": actions,
            "encoded_columns": encoded_cols,
            "frequency_columns": freq_cols,
            "datetime_features": dt_created,
            "log1p_columns": log_cols,
            "scaled_columns": scaled,
            "_dataframe": work,
            "_feature_columns": feature_columns,
            "_target_column": target_column,
        }

    def _resolve_target(
        self,
        context: dict[str, Any],
        instruction: str,
        df: pd.DataFrame,
    ) -> str | None:
        target = context.get("target_column") or context.get("_target_column")
        if not target and instruction:
            for part in instruction.replace(",", " ").split():
                if part.lower().startswith("target="):
                    target = part.split("=", 1)[1].strip()
                    break
        if target and target in df.columns:
            return str(target)
        return None

    def _detect_datetime_columns(self, df: pd.DataFrame) -> list[str]:
        found: list[str] = []
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                found.append(col)
                continue
            if df[col].dtype == object or str(df[col].dtype) == "string":
                # Sample parse — require decent success rate
                sample = df[col].dropna().astype(str).head(50)
                if len(sample) < 3:
                    continue
                parsed = pd.to_datetime(sample, errors="coerce")
                if parsed.notna().mean() >= 0.8:
                    # Avoid pure numeric strings
                    if sample.str.match(r"^\d+(\.\d+)?$").mean() < 0.5:
                        found.append(col)
        return found
