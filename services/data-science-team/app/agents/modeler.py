"""Modeler Agent — train a simple sklearn baseline model."""

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
    description = "Train a baseline RandomForest (classification or regression) and report metrics"

    async def run(self, context: dict[str, Any], instruction: str = "") -> dict[str, Any]:
        df: pd.DataFrame | None = context.get("dataframe")
        if df is None:
            return {
                "status": "error",
                "agent": self.name,
                "error": "No dataframe in context.",
            }

        # Resolve target: explicit context, instruction keyword, or last column heuristic
        target_column = context.get("target_column")
        if not target_column and instruction:
            # e.g. instruction="target=churn"
            for part in instruction.replace(",", " ").split():
                if part.lower().startswith("target="):
                    target_column = part.split("=", 1)[1].strip()
                    break

        if not target_column:
            # Prefer a column named like common targets, else last column
            candidates = [c for c in df.columns if c.lower() in {"target", "label", "y", "class", "churn"}]
            target_column = candidates[0] if candidates else df.columns[-1]

        if target_column not in df.columns:
            return {
                "status": "error",
                "agent": self.name,
                "error": f"Target column '{target_column}' not found. Columns: {list(df.columns)}",
            }

        feature_columns = context.get("feature_columns") or [
            c for c in df.columns if c != target_column
        ]
        # Keep only numeric features for sklearn baseline
        X = df[feature_columns].select_dtypes(include="number").copy()
        y = df[target_column].copy()

        if X.shape[1] == 0:
            return {
                "status": "error",
                "agent": self.name,
                "error": "No numeric feature columns available for modeling.",
            }

        # Drop rows with missing target
        mask = y.notna()
        X = X.loc[mask]
        y = y.loc[mask]

        if len(X) < 10:
            return {
                "status": "error",
                "agent": self.name,
                "error": f"Too few rows after filtering ({len(X)}). Need at least 10.",
            }

        # Infer task
        is_classification = self._is_classification(y)
        task = "classification" if is_classification else "regression"

        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.25, random_state=42, stratify=y if is_classification and y.nunique() > 1 else None
            )
        except ValueError:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.25, random_state=42
            )

        if is_classification:
            model = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42, n_jobs=-1)
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            metrics: dict[str, Any] = {
                "accuracy": float(accuracy_score(y_test, preds)),
                "f1_weighted": float(f1_score(y_test, preds, average="weighted", zero_division=0)),
            }
            if y.nunique() == 2:
                try:
                    proba = model.predict_proba(X_test)[:, 1]
                    metrics["roc_auc"] = float(roc_auc_score(y_test, proba))
                except Exception:
                    pass
        else:
            model = RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42, n_jobs=-1)
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            metrics = {
                "r2": float(r2_score(y_test, preds)),
                "mae": float(mean_absolute_error(y_test, preds)),
                "rmse": float(np.sqrt(mean_squared_error(y_test, preds))),
            }

        # Built-in impurity importance
        impurity_importance = sorted(
            [
                {"feature": f, "score": float(s)}
                for f, s in zip(X.columns, model.feature_importances_)
            ],
            key=lambda x: x["score"],
            reverse=True,
        )

        return {
            "status": "ok",
            "agent": self.name,
            "task": task,
            "target_column": target_column,
            "n_features_used": int(X.shape[1]),
            "n_train": int(len(X_train)),
            "n_test": int(len(X_test)),
            "metrics": metrics,
            "impurity_importance": impurity_importance[:20],
            "feature_columns_used": list(X.columns),
            "_dataframe": df,
            "_model": model,
            "_feature_columns": list(X.columns),
            "_target_column": target_column,
            "_X_train": X_train,
            "_y_train": y_train,
            "_X_test": X_test,
            "_y_test": y_test,
        }

    def _is_classification(self, y: pd.Series) -> bool:
        if y.dtype == object or str(y.dtype) == "category":
            return True
        nunique = y.nunique(dropna=True)
        if nunique <= 20 and set(pd.Series(y.dropna().unique()).map(type)) <= {int, np.integer, bool}:
            return True
        if nunique <= 10 and pd.api.types.is_integer_dtype(y):
            return True
        return False
