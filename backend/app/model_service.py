from __future__ import annotations

import json
import threading
from pathlib import Path

import joblib
import pandas as pd

from .config import settings
from .schemas import MachineInput

FEATURES = [
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]


class ModelService:
    def __init__(self, model_path: Path | None = None, manifest_path: Path | None = None) -> None:
        self.model_path = model_path or settings.model_path
        self.manifest_path = manifest_path or settings.manifest_path
        self.pipeline = None
        self.manifest: dict = {}
        self.error: str | None = None
        self._lock = threading.Lock()

    def load(self) -> None:
        try:
            self.pipeline = joblib.load(self.model_path)
            self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            manifest_features = [item["name"] for item in self.manifest["feature_schema"]]
            if manifest_features != FEATURES:
                raise ValueError("Model manifest feature schema does not match API schema")
            self.error = None
        except Exception as exc:  # startup must remain diagnosable through readiness
            self.pipeline = None
            self.error = f"Model unavailable: {type(exc).__name__}"

    @property
    def ready(self) -> bool:
        return self.pipeline is not None and not self.error

    def predict_many(self, rows: list[MachineInput]) -> list[dict]:
        if not self.ready:
            raise RuntimeError(self.error or "Model unavailable")
        frame = pd.DataFrame([row.feature_dict() for row in rows], columns=FEATURES)
        with self._lock:
            probabilities = self.pipeline.predict_proba(frame)[:, 1]
        threshold = float(self.manifest["threshold"])
        return [self._result(float(probability), threshold) for probability in probabilities]

    @staticmethod
    def _result(probability: float, threshold: float) -> dict:
        flagged = probability >= threshold
        risk = "high" if flagged else "medium" if probability >= threshold * 0.6 else "low"
        return {
            "probability": probability,
            "predicted_failure": flagged,
            "risk_level": risk,
            "result": "Failure Risk" if flagged else "Normal Operation",
            "recommendation": (
                "Prioritize a qualified inspection and review recent operating trends."
                if flagged
                else "Continue routine monitoring; this result does not replace physical inspection."
            ),
        }


model_service = ModelService()
