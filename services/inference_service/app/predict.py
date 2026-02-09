from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import joblib
import pandas as pd


EXPECTED_COLUMNS = [
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF",
]


def load_model(model_path: Path):
    model = joblib.load(model_path)
    return model


def _to_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert incoming JSON records to a DataFrame with the expected column names.
    Missing optional failure mode flags default to 0.
    """
    df = pd.DataFrame(records)

    # This code is to ensure the expected columns exist
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            # default 0 for mode flags; for core features, it’s an error
            if col in {"TWF", "HDF", "PWF", "OSF", "RNF"}:
                df[col] = 0
            else:
                raise ValueError(f"Missing required field: '{col}'")

    # Keep only expected columns and ignore extras
    df = df[EXPECTED_COLUMNS]
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