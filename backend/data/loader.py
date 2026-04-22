"""
Data loader: supports CSV, JSON, Parquet, Excel. Caches loaded DataFrames.
"""

import hashlib
import io
import os
from pathlib import Path
from typing import Dict

import pandas as pd

UPLOAD_DIR = Path(__file__).parent.parent.parent / "data" / "uploads"
SAMPLE_DIR = Path(__file__).parent.parent.parent / "data" / "samples"


class DataLoader:
    _cache: Dict[str, pd.DataFrame] = {}

    def load(self, dataset_id: str) -> pd.DataFrame:
        if dataset_id in self._cache:
            return self._cache[dataset_id]

        path = self._resolve_path(dataset_id)
        if path is None:
            raise FileNotFoundError(f"Dataset '{dataset_id}' not found")

        df = self._read_file(path)
        self._cache[dataset_id] = df
        return df

    def load_from_bytes(self, content: bytes, filename: str) -> tuple[str, pd.DataFrame]:
        dataset_id = hashlib.md5(content).hexdigest()[:12] + "_" + Path(filename).stem
        path = UPLOAD_DIR / filename
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        df = self._read_file(path)
        self._cache[dataset_id] = df
        return dataset_id, df

    def list_datasets(self) -> list[dict]:
        datasets = []
        for directory in [UPLOAD_DIR, SAMPLE_DIR]:
            if not directory.exists():
                continue
            for fp in directory.iterdir():
                if fp.suffix.lower() in {".csv", ".json", ".parquet", ".xlsx", ".xls"}:
                    datasets.append({
                        "id": fp.stem,
                        "name": fp.name,
                        "size_bytes": fp.stat().st_size,
                        "source": "upload" if directory == UPLOAD_DIR else "sample",
                        "path": str(fp),
                    })
        return datasets

    def invalidate(self, dataset_id: str):
        self._cache.pop(dataset_id, None)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_path(self, dataset_id: str) -> Path | None:
        for directory in [UPLOAD_DIR, SAMPLE_DIR]:
            for ext in [".csv", ".json", ".parquet", ".xlsx", ".xls"]:
                candidate = directory / (dataset_id + ext)
                if candidate.exists():
                    return candidate
        # Try exact path
        p = Path(dataset_id)
        if p.exists():
            return p
        return None

    def _read_file(self, path: Path) -> pd.DataFrame:
        ext = path.suffix.lower()
        if ext == ".csv":
            return pd.read_csv(path)
        elif ext == ".json":
            return pd.read_json(path)
        elif ext == ".parquet":
            return pd.read_parquet(path)
        elif ext in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
