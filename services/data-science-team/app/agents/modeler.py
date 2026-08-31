"""Modeler Agent — train baseline model; reuse FE train/test split when present."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from app.agents.base import BaseAgent


class ModelerAgent(BaseAgent):
    name = "modeler"
    description = "Train RandomForest; prefers train/test split from feature_engineer"

    async def run(self, context: dict[str, Any], instruction: str = "") -> dict[str, Any]:
        # Prefer pre-split from feature_engineer (train-fitted pipeline)
        X_train = context.get("_X_train") or context.get("X_train")
        X_test = context.get("_X_test") or context.get("X_test")
        y_train = context.get("_y_train") or context.get("y_train")
        y_test = context.get("_y_test") or context.get("y_test")
        target_column = context.get("target_column") or context.get("_target_column")
        split_source = "feature_engineer" if X_train is not None else None

        df: pd.DataFrame | None = context.get("dataframe")

        if X_train is None or y_train is None:
            if df is None:
                return {
                    "status": "error",
                    "agent": self.name,
                    "error": "No dataframe or pre-split data in context.",
                }
            target_column = self._resolve_target(context, instruction, df)
            if not target_column:
                candidates = [
                    c
                    for c in df.columns
                    if c.lower() in {"target", "label", "y", "class", "churn"}
                ]
                target_column = candidates[0] if candidates else df.columns[-1]

            if target_column not in df.columns:
                return {
                    "status": "error",
                    "agent": self.name,
                    "error": f"Target column '{target_column}' not found.",
                }

            feature_columns = context.get("feature_columns") or [
                c for c in df.columns if c != target_column
            ]
            X = df[feature_columns].select_dtypes(include="number").copy()
            y = df[target_column].copy()
            mask = y.notna()
            X, y = X.loc[mask], y.loc[mask]

            if X.shape[1] == 0:
                return {
                    "status": "error",
                    "agent": self.name,
                    "error": "No numeric feature columns available for modeling.",
                }
            if len(X) < 10:
                return {
                    "status": "error",
                    "agent": self.name,
                    "error": f"Too few rows ({len(X)}). Need at least 10.",
                }

            is_classification = self._is_classification(y)
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X,
                    y,
                    test_size=0.25,
                    random_state=42,
                    stratify=y if is_classification and y.nunique() > 1 else None,
                )
            except ValueError:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.25, random_state=42
                )
            split_source = "modeler"
        else:
            # Ensure numeric
            X_train = X_train.select_dtypes(include="number") if hasattr(X_train, "select_dtypes") else X_train
            X_test = X_test.select_dtypes(include="number") if hasattr(X_test, "select_dtypes") else X_test
            if X_test is None or y_test is None:
                return {
                    "status": "error",
                    "agent": self.name,
                    "error": "Incomplete train/test split in context.",
                }
            is_classification = self._is_classification(pd.Series(y_train))

        if X_train is None or y_train is None or X_test is None or y_test is None:
            return {
                "status": "error",
                "agent": self.name,
                "error": "Could not build train/test sets.",
            }

        task = "classification" if is_classification else "regression"

        if is_classification:
            model = RandomForestClassifier(
                n_estimators=50, max_depth=8, random_state=42, n_jobs=-1
            )
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            metrics: dict[str, Any] = {
                "accuracy": float(accuracy_score(y_test, preds)),
                "f1_weighted": float(
                    f1_score(y_test, preds, average="weighted", zero_division=0)
                ),
            }
            y_ser = pd.Series(y_train)
            if y_ser.nunique() == 2:
                try:
                    proba = model.predict_proba(X_test)[:, 1]
                    metrics["roc_auc"] = float(roc_auc_score(y_test, proba))
                except Exception:
                    pass
        else:
            model = RandomForestRegressor(
                n_estimators=50, max_depth=8, random_state=42, n_jobs=-1
            )
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            metrics = {
                "r2": float(r2_score(y_test, preds)),
                "mae": float(mean_absolute_error(y_test, preds)),
                "rmse": float(np.sqrt(mean_squared_error(y_test, preds))),
            }

        cols = list(X_train.columns) if hasattr(X_train, "columns") else []
        impurity_importance = sorted(
            [
                {"feature": str(f), "score": float(s)}
                for f, s in zip(cols, model.feature_importances_)
            ],
            key=lambda x: x["score"],
            reverse=True,
        )

        return {
            "status": "ok",
            "agent": self.name,
            "task": task,
            "target_column": target_column,
            "n_features_used": int(X_train.shape[1]),
            "n_train": int(len(X_train)),
            "n_test": int(len(X_test)),
            "split_source": split_source,
            "metrics": metrics,
            "impurity_importance": impurity_importance[:20],
            "feature_columns_used": cols,
            "_dataframe": df,
            "_model": model,
            "_feature_columns": cols,
            "_target_column": target_column,
            "_X_train": X_train,
            "_y_train": y_train,
            "_X_test": X_test,
            "_y_test": y_test,
        }

    def _resolve_target(
        self, context: dict[str, Any], instruction: str, df: pd.DataFrame
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

    def _is_classification(self, y: pd.Series) -> bool:
        y = pd.Series(y)
        if y.dtype == object or str(y.dtype) == "category":
            return True
        nunique = y.nunique(dropna=True)
        if nunique <= 20 and set(pd.Series(y.dropna().unique()).map(type)) <= {
            int,
            np.integer,
            bool,
        }:
            return True
        if nunique <= 10 and pd.api.types.is_integer_dtype(y):
            return True
        return False
