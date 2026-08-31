"""Data Loader Agent — discovers and loads tabular data."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pandas as pd

from app.agents.base import BaseAgent


class DataLoaderAgent(BaseAgent):
    name = "data_loader"
    description = "Load CSV, Parquet, Excel or in-memory tabular data"

    async def run(self, context: dict[str, Any], instruction: str = "") -> dict[str, Any]:
        """
        Expected context keys (one of):
          - path: str (local file path)
          - content: bytes | str (raw file content)
          - filename: str (used with content to detect format)
          - dataframe: already loaded pandas DataFrame (pass-through)
        """
        if "dataframe" in context and context["dataframe"] is not None:
            df = context["dataframe"]
            source = "context.dataframe"
        elif "path" in context and context["path"]:
            path = Path(context["path"])
            df = self._load_from_path(path)
            source = str(path)
        elif "content" in context and context["content"] is not None:
            filename = context.get("filename", "data.csv")
            df = self._load_from_bytes(context["content"], filename)
            source = filename
        else:
            return {
                "status": "error",
                "agent": self.name,
                "error": "No path, content, or dataframe provided",
            }

        preview = df.head(5).to_dict(orient="records")
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}

        return {
            "status": "ok",
            "agent": self.name,
            "source": source,
            "shape": list(df.shape),
            "columns": list(df.columns),
            "dtypes": dtypes,
            "preview": preview,
            "null_counts": df.isnull().sum().to_dict(),
            # Keep the actual frame in context for downstream agents
            "_dataframe": df,
        }

    def _load_from_path(self, path: Path) -> pd.DataFrame:
        suffix = path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(path)
        if suffix in {".parquet", ".pq"}:
            return pd.read_parquet(path)
        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        if suffix == ".json":
            return pd.read_json(path)
        raise ValueError(f"Unsupported file type: {suffix}")

    def _load_from_bytes(self, content: bytes | str, filename: str) -> pd.DataFrame:
        if isinstance(content, str):
            content = content.encode("utf-8")
        buffer = io.BytesIO(content)
        suffix = Path(filename).suffix.lower()

        if suffix == ".csv":
            return pd.read_csv(buffer)
        if suffix in {".parquet", ".pq"}:
            return pd.read_parquet(buffer)
        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(buffer)
        if suffix == ".json":
            return pd.read_json(buffer)
        # Default to CSV
        buffer.seek(0)
        return pd.read_csv(buffer)
