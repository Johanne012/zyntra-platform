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
            "import pandas as pd",
            "import numpy as np",
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
                    "from sklearn.metrics import accuracy_score, f1_score, r2_score, mean_absolute_error",
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
            lines.extend(
                [
                    "# --- Feature engineering ---",
                    "# Drop very high-cardinality object columns",
                    "for col in list(df.select_dtypes(include=['object', 'string']).columns):",
                    "    if df[col].nunique(dropna=True) > max(50, int(0.5 * len(df))):",
                    "        df = df.drop(columns=[col])",
                    "cat_cols = [c for c in df.select_dtypes(include=['object', 'string', 'category']).columns",
                    "            if df[c].nunique(dropna=True) <= 20]",
                    "if cat_cols:",
                    "    df = pd.get_dummies(df, columns=cat_cols, dummy_na=False)",
                    "num_cols = df.select_dtypes(include='number').columns",
                    "for col in num_cols:",
                    "    std = df[col].std()",
                    "    if std and std > 0:",
                    "        df[col] = (df[col] - df[col].mean()) / std",
                    "print('features', df.shape)",
                    "",
                ]
            )

        if "modeler" in steps_covered:
            tgt = target or "TARGET_COLUMN"
            lines.extend(
                [
                    "# --- Model ---",
                    f"TARGET = "{tgt}"  # set explicitly if auto-detect was used",
                    "if TARGET not in df.columns:",
                    "    raise SystemExit(f'Target {TARGET!r} missing: {list(df.columns)}')",
                    "feature_cols = [c for c in df.select_dtypes(include='number').columns if c != TARGET]",
                    "X = df[feature_cols]",
                    "y = df[TARGET]",
                    "mask = y.notna()",
                    "X, y = X.loc[mask], y.loc[mask]",
                    "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)",
                    "# Task heuristic: few unique ints => classification",
                    "is_clf = y.nunique() <= 20 and str(y.dtype).startswith(('int', 'bool', 'object', 'category'))",
                    "if is_clf:",
                    "    model = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42)",
                    "else:",
                    "    model = RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42)",
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

        lines.extend(
            [
                "# --- Done ---",
                "print('Pipeline script finished.')",
                "",
            ]
        )

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
