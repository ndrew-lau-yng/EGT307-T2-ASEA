import json
from pathlib import Path
from collections import Counter

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.ensemble import RandomForestClassifier

from imblearn.over_sampling import SMOTE


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRAIN_CSV = PROJECT_ROOT / "data" / "raw" / "train.csv"
TEST_CSV  = PROJECT_ROOT / "data" / "raw" / "test.csv"

# Match your renamed folder
MODEL_OUT   = PROJECT_ROOT / "services" / "inference_service" / "model" / "model.joblib"
METRICS_OUT = PROJECT_ROOT / "training" / "outputs" / "metrics.json"
SAMPLES_OUT = PROJECT_ROOT / "data" / "samples" / "sample_requests.json"

TARGET_COL = "Machine failure"

# Kaggle notebook drops
DROP_COLS = ["id", "Product ID"]
FAILURE_MODE_COLS = ["TWF", "HDF", "PWF", "OSF", "RNF"]


def ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def main():
    if not TRAIN_CSV.exists():
        raise FileNotFoundError(f"Missing: {TRAIN_CSV}")
    if not TEST_CSV.exists():
        raise FileNotFoundError(f"Missing: {TEST_CSV}")

    df = pd.read_csv(TRAIN_CSV)
    test_df = pd.read_csv(TEST_CSV)

    if TARGET_COL not in df.columns:
        raise ValueError(f"Target column '{TARGET_COL}' not found in train.csv")

    for c in DROP_COLS:
        if c in df.columns:
            df.drop(columns=[c], inplace=True)
        if c in test_df.columns:
            test_df.drop(columns=[c], inplace=True)

    for c in FAILURE_MODE_COLS:
        if c in df.columns:
            df.drop(columns=[c], inplace=True)
        if c in test_df.columns:
            test_df.drop(columns=[c], inplace=True)

    y = df.pop(TARGET_COL).astype(int)
    X = df

    if "Type" in X.columns:
        le = LabelEncoder()
        X["Type"] = le.fit_transform(X["Type"])

        if "Type" in test_df.columns:
            mapping = {cls: int(i) for i, cls in enumerate(le.classes_)}
            test_df["Type"] = test_df["Type"].map(mapping).fillna(-1).astype(int)

    print("Class distribution before SMOTE:", Counter(y))

    smote = SMOTE(random_state=42)
    X_resampled, y_resampled = smote.fit_resample(X, y)

    print("Class distribution after SMOTE:", Counter(y_resampled))

    X_train, X_val, y_train, y_val = train_test_split(
        X_resampled, y_resampled, test_size=0.1, random_state=42
    )

    # RandomForest only
    model = RandomForestClassifier(random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_val)

    metrics = {
        "accuracy": float(accuracy_score(y_val, y_pred)),
        "precision": float(precision_score(y_val, y_pred, zero_division=0)),
        "recall": float(recall_score(y_val, y_pred, zero_division=0)),
        "f1": float(f1_score(y_val, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_val, y_pred).tolist(),
        "notes": [
            "This follows the Kaggle notebook: LabelEncoder(Type), drop failure modes, SMOTE before split (leakage).",
            "Use the pipeline-based SMOTE-after-split approach for a realistic evaluation.",
        ],
        "features_used": list(X.columns),
    }

    ensure_parent(MODEL_OUT)
    ensure_parent(METRICS_OUT)
    ensure_parent(SAMPLES_OUT)

    joblib.dump(model, MODEL_OUT)
    METRICS_OUT.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    # Save demo samples in the format for FastAPI
    sample_cols = list(X.columns)
    missing = [c for c in sample_cols if c not in test_df.columns]
    if missing:
        raise ValueError(f"test.csv missing columns expected by model: {missing}")

    samples = test_df[sample_cols].sample(n=5, random_state=42).to_dict(orient="records")
    SAMPLES_OUT.write_text(json.dumps({"records": samples}, indent=2), encoding="utf-8")

    print("Saved model:", MODEL_OUT)
    print("Saved metrics:", METRICS_OUT)
    print("Saved demo samples:", SAMPLES_OUT)
    print("Validation F1:", metrics["f1"])


if __name__ == "__main__":
    main()