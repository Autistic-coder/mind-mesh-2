from dataclasses import replace

from fastapi.testclient import TestClient

from backend.app import main


def test_registration_restoration_logout(client: TestClient):
    payload = {
        "email": "student@example.com",
        "display_name": "Student",
        "password": "correct-horse-battery",
    }
    registered = client.post("/api/auth/register", json=payload)
    assert registered.status_code == 201
    assert "mindmesh_session" in client.cookies
    assert client.get("/api/auth/me").json()["email"] == payload["email"]
    assert client.get("/api/auth/csrf").json()["csrf_token"] == client.cookies["mindmesh_csrf"]
    csrf = client.cookies["mindmesh_csrf"]
    assert client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 204
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/csrf").status_code == 401


def test_login_uses_generic_error(client: TestClient):
    client.post(
        "/api/auth/register",
        json={"email": "a@example.com", "display_name": "Alpha", "password": "long-password-123"},
    )
    csrf = client.cookies["mindmesh_csrf"]
    client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
    wrong = client.post("/api/auth/login", json={"email": "a@example.com", "password": "wrong"})
    missing = client.post(
        "/api/auth/login", json={"email": "missing@example.com", "password": "wrong"}
    )
    assert wrong.status_code == missing.status_code == 401
    assert wrong.json() == missing.json()


def test_duplicate_registration_and_password_validation(client: TestClient):
    payload = {
        "email": "dup@example.com",
        "display_name": "Duplicate",
        "password": "long-password-123",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409
    assert (
        client.post(
            "/api/auth/register", json={**payload, "email": "new@example.com", "password": "short"}
        ).status_code
        == 422
    )


def test_csrf_is_required(client: TestClient, account, machine):
    assert client.post("/api/predictions", json=machine).status_code == 403
    assert (
        client.post("/api/predictions", json=machine, headers={"X-CSRF-Token": "wrong"}).status_code
        == 403
    )


def test_login_rate_limit(client: TestClient):
    payload = {"email": "nobody@example.com", "password": "wrong"}
    statuses = [client.post("/api/auth/login", json=payload).status_code for _ in range(9)]
    assert statuses[-1] == 429


def test_production_session_cookie_supports_cross_site_frontend(client: TestClient, monkeypatch):
    monkeypatch.setattr(main, "settings", replace(main.settings, secure_cookies=True))
    response = client.post(
        "/api/auth/register",
        json={
            "email": "cookie@example.com",
            "display_name": "Cookie Test",
            "password": "long-password-123",
        },
    )
    cookies = response.headers.get_list("set-cookie")
    session = next(value for value in cookies if value.startswith("mindmesh_session="))
    assert "HttpOnly" in session
    assert "SameSite=none" in session
    assert "Secure" in session
