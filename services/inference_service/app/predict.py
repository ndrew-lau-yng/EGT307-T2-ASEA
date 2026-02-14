from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import joblib
import pandas as pd


# Code is to choose columns I want and drop the rest later
EXPECTED_COLUMNS = [
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]

TYPE_MAP = {"H": 0, "L": 1, "M": 2}


def load_model(model_path: Path):
    return joblib.load(model_path)


def _encode_type(v: Any) -> int:
    if isinstance(v, (int, float)) and not pd.isna(v):
        return int(v)

    if v is None:
        raise ValueError("Missing required field: 'Type'")

    s = str(v).strip().upper()
    if s not in TYPE_MAP:
        raise ValueError(f"Invalid Type '{v}'. Must be one of {list(TYPE_MAP.keys())}")
    return TYPE_MAP[s]


def _to_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(records)

    # ensure the required columns exist
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"Missing required field: '{col}'")

    # keep only the expected columns
    df = df[EXPECTED_COLUMNS].copy()

    # encode Type exactly like training
    df["Type"] = df["Type"].apply(_encode_type)

    for col in EXPECTED_COLUMNS:
        if col != "Type":
            df[col] = pd.to_numeric(df[col], errors="raise")

    return df


def predict(model, records: List[Dict[str, Any]]) -> Tuple[List[int], Optional[List[float]]]:
    df = _to_dataframe(records)

    preds = model.predict(df).tolist()

    probs = None
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(df)
        if proba.shape[1] >= 2:
            probs = proba[:, 1].tolist()

    return preds, probs