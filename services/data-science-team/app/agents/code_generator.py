"""Code Generator Agent — emit reproducible Python from pipeline results."""

from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent


class CodeGeneratorAgent(BaseAgent):
    name = "code_generator"
    description = "Generate a reproducible Python script reflecting pipeline steps"

    async def run(self, context: dict[str, Any], instruction: str = "") -> dict[str, Any]:
        results: list[dict[str, Any]] = context.get("pipeline_results") or []
        source = context.get("source_filename") or context.get("filename") or "data.csv"
        target = context.get("target_column") or context.get("_target_column")

        steps_covered = [r.get("agent") for r in results if r.get("status") == "ok"]

        lines: list[str] = [
            "# -*- coding: utf-8 -*-",
            '"""',
            "ZYNTRA Data Science Team — reproducible pipeline script",
            "Auto-generated. Review before production use.",
            '"""',
            "from __future__ import annotations",
            "",
            "import numpy as np",
            "import pandas as pd",
            "",
        ]

        need_sklearn = any(
            s in steps_covered for s in ("feature_engineer", "modeler", "interpretability")
        )
        if need_sklearn:
            lines.extend(
                [
                    "from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor",
                    "from sklearn.model_selection import train_test_split",
                    "from sklearn.inspection import permutation_importance",
                    "",
                ]
            )

        lines.append("# --- Load ---")
        lines.append(f'SOURCE = "{source}"')
        lines.append("df = pd.read_csv(SOURCE)  # adjust if parquet/excel")
        lines.append("print('shape', df.shape)")
        lines.append("")

        if "cleaner" in steps_covered:
            lines.extend(
                [
                    "# --- Clean ---",
                    "df = df.dropna(how='all')",
                    "df = df.drop_duplicates()",
                    "for col in df.select_dtypes(include=['object', 'string']).columns:",
                    "    df[col] = df[col].astype(str).str.strip().replace({'nan': pd.NA, 'None': pd.NA, '': pd.NA})",
                    "for col in df.select_dtypes(include='number').columns:",
                    "    if df[col].isna().any():",
                    "        df[col] = df[col].fillna(df[col].median())",
                    "for col in df.select_dtypes(include=['object', 'string', 'category']).columns:",
                    "    if df[col].isna().any():",
                    "        mode = df[col].mode(dropna=True)",
                    "        df[col] = df[col].fillna(mode.iloc[0] if len(mode) else 'unknown')",
                    "print('after clean', df.shape)",
                    "",
                ]
            )

        if "eda" in steps_covered:
            lines.extend(
                [
                    "# --- EDA (summary) ---",
                    "print(df.describe(include='all').T.head(20))",
                    "print('nulls', df.isna().sum().to_dict())",
                    "",
                ]
            )

        if "feature_engineer" in steps_covered:
            tgt = target or "TARGET_COLUMN"
            lines.extend(
                [
                    "# --- Feature engineering (mirrors service logic, simplified) ---",
                    f"TARGET = "{tgt}"",
                    "feature_df = df.drop(columns=[TARGET], errors='ignore').copy()",
                    "# Datetime-like object columns",
                    "for col in list(feature_df.columns):",
                    "    if feature_df[col].dtype == object:",
                    "        sample = feature_df[col].dropna().astype(str).head(50)",
                    "        if len(sample) >= 3:",
                    "            parsed = pd.to_datetime(sample, errors='coerce')",
                    "            if parsed.notna().mean() >= 0.8:",
                    "                p = pd.to_datetime(feature_df[col], errors='coerce')",
                    "                feature_df[f'{col}_month'] = p.dt.month",
                    "                feature_df[f'{col}_dayofweek'] = p.dt.dayofweek",
                    "                feature_df = feature_df.drop(columns=[col])",
                    "# Frequency encode mid-cardinality categoricals",
                    "for col in list(feature_df.select_dtypes(include=['object', 'string', 'category']).columns):",
                    "    n = feature_df[col].nunique(dropna=True)",
                    "    if 20 < n <= 100:",
                    "        freq = feature_df[col].value_counts(dropna=False)",
                    "        feature_df[f'{col}_freq'] = feature_df[col].map(freq).astype(float)",
                    "        feature_df = feature_df.drop(columns=[col])",
                    "    elif n <= 20:",
                    "        feature_df = pd.get_dummies(feature_df, columns=[col], dummy_na=False)",
                    "    else:",
                    "        feature_df = feature_df.drop(columns=[col])",
                    "# log1p + robust scale numerics",
                    "for col in feature_df.select_dtypes(include='number').columns:",
                    "    s = feature_df[col].astype(float)",
                    "    if s.notna().sum() >= 3 and (s.dropna() >= 0).all() and abs(float(s.skew())) > 1.0:",
                    "        s = np.log1p(s)",
                    "        feature_df[col] = s",
                    "    median, q1, q3 = float(s.median()), float(s.quantile(0.25)), float(s.quantile(0.75))",
                    "    iqr = q3 - q1",
                    "    if iqr > 0:",
                    "        feature_df[col] = (s - median) / iqr",
                    "if TARGET in df.columns:",
                    "    feature_df[TARGET] = df[TARGET].values",
                    "df = feature_df",
                    "print('features', df.shape)",
                    "",
                ]
            )

        if "modeler" in steps_covered:
            tgt = target or "TARGET_COLUMN"
            lines.extend(
                [
                    "# --- Model ---",
                    f"TARGET = "{tgt}"",
                    "if TARGET not in df.columns:",
                    "    raise SystemExit(f'Target {TARGET!r} missing: {list(df.columns)}')",
                    "feature_cols = [c for c in df.select_dtypes(include='number').columns if c != TARGET]",
                    "X = df[feature_cols]",
                    "y = df[TARGET]",
                    "mask = y.notna()",
                    "X, y = X.loc[mask], y.loc[mask]",
                    "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)",
                    "is_clf = y.nunique() <= 20",
                    "model = (",
                    "    RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42)",
                    "    if is_clf else",
                    "    RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42)",
                    ")",
                    "model.fit(X_train, y_train)",
                    "print('score', model.score(X_test, y_test))",
                    "",
                ]
            )

        if "interpretability" in steps_covered:
            lines.extend(
                [
                    "# --- Interpretability ---",
                    "r = permutation_importance(model, X_test, y_test, n_repeats=5, random_state=42)",
                    "imp = sorted(zip(feature_cols, r.importances_mean), key=lambda t: t[1], reverse=True)",
                    "print('top features', imp[:15])",
                    "",
                ]
            )

        lines.extend(["# --- Done ---", "print('Pipeline script finished.')", ""])
        script = "\n".join(lines)

        return {
            "status": "ok",
            "agent": self.name,
            "language": "python",
            "script": script,
            "filename_suggestion": "zyntra_pipeline_repro.py",
            "steps_covered": steps_covered,
            "n_lines": len(lines),
        }
