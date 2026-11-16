from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

FEATURES = [
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]
TARGET = "Machine failure"
LEAKAGE_COLUMNS = ["UDI", "UID", "Product ID", "TWF", "HDF", "PWF", "OSF", "RNF"]
SEED = 42


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(df: pd.DataFrame) -> None:
    required = set(FEATURES + [TARGET])
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if len(df) < 1000 or df[FEATURES + [TARGET]].isna().any().any():
        raise ValueError("Dataset is too small or contains missing required values")
    if set(df["Type"].unique()) != {"L", "M", "H"} or not set(df[TARGET].unique()) <= {0, 1}:
        raise ValueError("Unexpected Type or target values")
    if any(column in FEATURES for column in LEAKAGE_COLUMNS):
        raise ValueError("Leakage column included in features")


def metrics(y_true, probability, threshold: float) -> dict:
    predicted = probability >= threshold
    matrix = confusion_matrix(y_true, predicted)
    return {
        "accuracy": accuracy_score(y_true, predicted),
        "precision": precision_score(y_true, predicted, zero_division=0),
        "recall": recall_score(y_true, predicted, zero_division=0),
        "f1": f1_score(y_true, predicted, zero_division=0),
        "roc_auc": roc_auc_score(y_true, probability),
        "confusion_matrix": matrix.tolist(),
        "false_negatives": int(matrix[1, 0]),
        "false_positives": int(matrix[0, 1]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/raw/ai4i2020.csv"))
    parser.add_argument("--output", type=Path, default=Path("model"))
    args = parser.parse_args()
    df = pd.read_csv(args.data)
    validate(df)
    X, y = df[FEATURES], df[TARGET].astype(int)
    X_train, X_hold, y_train, y_hold = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=SEED
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_hold, y_hold, test_size=0.50, stratify=y_hold, random_state=SEED
    )
    preprocessor = ColumnTransformer(
        [("type", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["Type"])],
        remainder="passthrough",
        verbose_feature_names_out=False,
    )
    forest = RandomForestClassifier(
        n_estimators=500,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=SEED,
        n_jobs=1,
    )
    pipeline = Pipeline([("preprocessor", preprocessor), ("classifier", forest)])
    pipeline.fit(X_train, y_train)
    val_probability = pipeline.predict_proba(X_val)[:, 1]
    thresholds = np.linspace(0.05, 0.8, 151)
    threshold = float(
        max(
            thresholds,
            key=lambda value: (
                f1_score(y_val, val_probability >= value),
                recall_score(y_val, val_probability >= value),
            ),
        )
    )
    test_probability = pipeline.predict_proba(X_test)[:, 1]
    test_metrics = metrics(y_test, test_probability, threshold)
    baseline = {
        "strategy": "always_normal",
        "accuracy": float((y_test == 0).mean()),
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
    }
    transformed = pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()
    importances = sorted(
        (
            {"feature": name, "importance": float(value)}
            for name, value in zip(transformed, forest.feature_importances_, strict=True)
        ),
        key=lambda item: item["importance"],
        reverse=True,
    )
    manifest = {
        "model_version": "1.0.0",
        "trained_at": datetime.now(UTC).isoformat(),
        "dataset": "AI4I 2020 Predictive Maintenance Dataset",
        "dataset_source": "UCI Machine Learning Repository",
        "dataset_sha256": file_hash(args.data),
        "record_count": len(df),
        "random_seed": SEED,
        "split": {
            "train": len(X_train),
            "validation": len(X_val),
            "test": len(X_test),
            "stratified": True,
        },
        "feature_schema": [
            {"name": name, "type": "categorical" if name == "Type" else "number"}
            for name in FEATURES
        ],
        "target": TARGET,
        "excluded_columns": LEAKAGE_COLUMNS,
        "threshold": threshold,
        "class_distribution": {
            str(key): int(value) for key, value in y.value_counts().sort_index().items()
        },
        "random_forest": forest.get_params(),
        "metrics": test_metrics,
        "baseline": baseline,
        "feature_importance": importances,
        "library_versions": {
            "scikit_learn": sklearn.__version__,
            "pandas": pd.__version__,
            "joblib": joblib.__version__,
        },
    }
    args.output.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, args.output / "mindmesh_rf_v1.joblib", compress=3)
    (args.output / "model_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
