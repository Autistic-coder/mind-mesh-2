from fastapi.testclient import TestClient

from backend.app.model_service import FEATURES, ModelService, model_service
from backend.app.schemas import MachineInput


def test_health_and_readiness(client: TestClient):
    assert client.get("/api/health").json() == {"status": "ok"}
    ready = client.get("/api/ready")
    assert ready.status_code == 200
    assert ready.json()["model_version"] == "1.0.0"


def test_prediction_persists_actual_inference(client: TestClient, csrf, machine):
    response = client.post("/api/predictions", json=machine, headers={"X-CSRF-Token": csrf})
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["probability"] <= 1
    assert body["model_version"] == "1.0.0"
    history = client.get("/api/predictions").json()
    assert history["total"] == 1
    assert history["items"][0]["id"] == body["id"]


def test_training_and_api_schema_and_probability_match(client: TestClient, csrf, machine):
    manifest_names = [item["name"] for item in model_service.manifest["feature_schema"]]
    assert manifest_names == FEATURES
    expected = model_service.predict_many([MachineInput.model_validate(machine)])[0]
    actual = client.post("/api/predictions", json=machine, headers={"X-CSRF-Token": csrf}).json()
    assert actual["probability"] == expected["probability"]
    assert actual["predicted_failure"] == expected["predicted_failure"]


def test_invalid_prediction_input(client: TestClient, csrf, machine):
    invalid = {**machine, "Torque [Nm]": 500}
    response = client.post("/api/predictions", json=invalid, headers={"X-CSRF-Token": csrf})
    assert response.status_code == 422


def test_account_isolation(client: TestClient, csrf, machine):
    created = client.post("/api/predictions", json=machine, headers={"X-CSRF-Token": csrf}).json()
    client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
    client.post(
        "/api/auth/register",
        json={
            "email": "other@example.com",
            "display_name": "Other User",
            "password": "another-password-123",
        },
    )
    assert client.get(f"/api/predictions/{created['id']}").status_code == 404
    assert client.get("/api/predictions").json()["total"] == 0


def test_delete_requires_ownership(client: TestClient, csrf, machine):
    created = client.post("/api/predictions", json=machine, headers={"X-CSRF-Token": csrf}).json()
    client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
    client.post(
        "/api/auth/register",
        json={
            "email": "other2@example.com",
            "display_name": "Other User",
            "password": "another-password-123",
        },
    )
    other_csrf = client.cookies["mindmesh_csrf"]
    assert (
        client.delete(
            f"/api/predictions/{created['id']}", headers={"X-CSRF-Token": other_csrf}
        ).status_code
        == 404
    )


def test_missing_model_artifact_is_reported(tmp_path):
    service = ModelService(tmp_path / "missing.joblib", tmp_path / "missing.json")
    service.load()
    assert not service.ready
    assert service.error.startswith("Model unavailable")
