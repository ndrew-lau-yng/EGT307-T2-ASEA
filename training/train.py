import json
from pathlib import Path

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.ensemble import RandomForestClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRAIN_CSV = PROJECT_ROOT / "data" / "raw" / "train.csv"
TEST_CSV  = PROJECT_ROOT / "data" / "raw" / "test.csv"

MODEL_OUT = PROJECT_ROOT / "services" / "inference-service" / "model" / "model.joblib"
METRICS_OUT = PROJECT_ROOT / "training" / "outputs" / "metrics.json"
SAMPLES_OUT = PROJECT_ROOT / "data" / "samples" / "sample_requests.json"


TARGET_COL = "Machine failure"

DROP_COLS = ["id", "Product ID"]
CAT_COLS = ["Type"]
NUM_COLS = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]

MODE_COLS = ["TWF", "HDF", "PWF", "OSF", "RNF"]
NUM_COLS += MODE_COLS


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

    y = df[TARGET_COL].astype(int)
    X = df.drop(columns=[TARGET_COL])

    for c in DROP_COLS:
        if c in X.columns:
            X = X.drop(columns=[c])
        if c in test_df.columns:
            test_df = test_df.drop(columns=[c])

    categorical = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])

    numeric = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", categorical, CAT_COLS),
            ("num", numeric, NUM_COLS),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )

    clf = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced",
    )

    pipe = Pipeline(steps=[
        ("prep", preprocessor),
        ("model", clf),
    ])

    X_train, X_val, y_train, y_val = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_val)

    metrics = {
        "accuracy": float(accuracy_score(y_val, y_pred)),
        "precision": float(precision_score(y_val, y_pred, zero_division=0)),
        "recall": float(recall_score(y_val, y_pred, zero_division=0)),
        "f1": float(f1_score(y_val, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_val, y_pred).tolist(),
        "features_used": {
            "categorical": CAT_COLS,
            "numeric": NUM_COLS,
            "dropped": DROP_COLS,
        }
    }

    ensure_parent(MODEL_OUT)
    ensure_parent(METRICS_OUT)
    ensure_parent(SAMPLES_OUT)

    joblib.dump(pipe, MODEL_OUT)
    METRICS_OUT.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    sample_cols = CAT_COLS + NUM_COLS
    missing = [c for c in sample_cols if c not in test_df.columns]
    if missing:
        raise ValueError(f"test.csv missing columns expected by model: {missing}")

    samples = test_df[sample_cols].sample(n=5, random_state=42).to_dict(orient="records")
    SAMPLES_OUT.write_text(json.dumps(samples, indent=2), encoding="utf-8")

    print("Saved model:", MODEL_OUT)
    print("Saved metrics:", METRICS_OUT)
    print("Saved demo samples:", SAMPLES_OUT)
    print("Validation F1:", metrics["f1"])


if __name__ == "__main__":
    main()