from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB = Path(__file__).parent / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["SECURE_COOKIES"] = "false"

from backend.app.database import Base, engine  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.app.security import clear_rate_limits  # noqa: E402


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    clear_rate_limits()
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(engine)
    engine.dispose()
    TEST_DB.unlink(missing_ok=True)


@pytest.fixture
def account(client: TestClient):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "owner@example.com",
            "display_name": "Machine Owner",
            "password": "safe-password-123",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def csrf(client: TestClient, account):
    return client.cookies["mindmesh_csrf"]


@pytest.fixture
def machine():
    return {
        "Type": "L",
        "Air temperature [K]": 298.1,
        "Process temperature [K]": 308.6,
        "Rotational speed [rpm]": 1551,
        "Torque [Nm]": 42.8,
        "Tool wear [min]": 0,
    }
