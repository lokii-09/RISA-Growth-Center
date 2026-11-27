from __future__ import annotations

import pandas as pd


def foreign_key_check(frame: pd.DataFrame, key: str, parent: pd.DataFrame, parent_key: str) -> pd.Series:
    known = set(parent[parent_key].dropna())
    return frame[key].notna() & ~frame[key].isin(known)


def missing_numeric_check(frame: pd.DataFrame, columns: list[str]) -> dict[str, int]:
    return {column: int(frame[column].isna().sum()) for column in columns if column in frame.columns}


def invalid_categories(frame: pd.DataFrame, column: str, allowed: set[str]) -> pd.Series:
    values = frame[column].dropna()
    return frame[column].isin(values) & ~frame[column].isin(allowed)
