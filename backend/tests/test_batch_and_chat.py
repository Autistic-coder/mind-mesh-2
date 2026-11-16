import io

from fastapi.testclient import TestClient

from backend.app.main import csv_safe


def csv_file(rows: str) -> dict:
    header = "Type,Air temperature [K],Process temperature [K],Rotational speed [rpm],Torque [Nm],Tool wear [min]\n"
    return {"file": ("machines.csv", io.BytesIO((header + rows).encode()), "text/csv")}


def test_batch_validation_and_results_download(client: TestClient, csrf):
    response = client.post(
        "/api/batches",
        files=csv_file("L,298.1,308.6,1551,42.8,0\nM,299,309,1400,48,120\n"),
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["row_count"] == 2
    download = client.get(f"/api/batches/{body['id']}/download")
    assert download.status_code == 200
    assert "Failure probability" in download.text


def test_batch_row_errors_are_bounded_and_descriptive(client: TestClient, csrf):
    response = client.post(
        "/api/batches", files=csv_file("L,500,308.6,1551,42.8,0\n"), headers={"X-CSRF-Token": csrf}
    )
    assert response.status_code == 422
    assert response.json()["detail"]["errors"][0]["row"] == 2


def test_csv_formula_injection_protection():
    assert csv_safe("=2+2") == "'=2+2"
    assert csv_safe("@SUM(A1)") == "'@SUM(A1)"
    assert csv_safe("safe") == "safe"


def test_static_help_without_openai_key(client: TestClient, csrf):
    response = client.post(
        "/api/conversations",
        json={"message": "What is torque?", "share_prediction": False},
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 200
    assert response.json()["mode"] == "static"
    assert response.json()["reply"].startswith("Static help:")


def test_conversation_ownership(client: TestClient, csrf):
    client.post(
        "/api/conversations",
        json={"message": "Explain recall", "share_prediction": False},
        headers={"X-CSRF-Token": csrf},
    )
    assert len(client.get("/api/conversations").json()) == 2
    client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
    client.post(
        "/api/auth/register",
        json={
            "email": "chat2@example.com",
            "display_name": "Chat Two",
            "password": "another-password-123",
        },
    )
    assert client.get("/api/conversations").json() == []
