from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./mindmesh.db")
    model_path: Path = Path(os.getenv("MODEL_PATH", ROOT / "model" / "mindmesh_rf_v1.joblib"))
    manifest_path: Path = Path(
        os.getenv("MODEL_MANIFEST_PATH", ROOT / "model" / "model_manifest.json")
    )
    frontend_origins: tuple[str, ...] = tuple(
        value.strip()
        for value in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",")
        if value.strip()
    )
    secure_cookies: bool = _bool("SECURE_COOKIES")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    session_days: int = int(os.getenv("SESSION_DAYS", "7"))
    max_batch_rows: int = int(os.getenv("MAX_BATCH_ROWS", "500"))


settings = Settings()
