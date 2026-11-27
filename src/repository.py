from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from .models import CanonicalDataset


class Repository:
    """Reusable read-only accessor for cleaned Phase 0 tables."""

    def __init__(self, dataset: CanonicalDataset):
        self.dataset = dataset

    def table(self, name: str) -> pd.DataFrame:
        if name not in self.dataset.working:
            raise KeyError(f"Unknown table '{name}'")
        return self.dataset.working[name].copy(deep=True)

    def reset(self) -> None:
        self.dataset.working = {
            name: frame.copy(deep=True) for name, frame in self.dataset.original.items()
        }

    def export_working_csv(self, directory: str | Path) -> None:
        output = Path(directory)
        output.mkdir(parents=True, exist_ok=True)
        for name, frame in self.dataset.working.items():
            filename = name.lower().replace(" ", "_").replace("-", "_") + ".csv"
            frame.to_csv(output / filename, index=False)
