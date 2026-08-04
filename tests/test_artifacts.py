import pytest
from botocore.exceptions import EndpointConnectionError
from fastapi.testclient import TestClient

from app.main import app


TEST_API_KEY = "unit-test-api-key"
AUTH_HEADERS = {"X-API-Key": TEST_API_KEY}

client = TestClient(app)


@pytest.fixture(autouse=True)
def configure_test_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", TEST_API_KEY)


def test_create_artifact(monkeypatch: pytest.MonkeyPatch) -> None:
    stored: dict[str, str] = {}

    def fake_upload(name: str, content: str) -> None:
        stored[name] = content

    monkeypatch.setattr("app.main.upload_artifact", fake_upload)

    response = client.post(
        "/artifacts",
        headers=AUTH_HEADERS,
        json={
            "name": "security-report.txt",
            "content": "No critical vulnerabilities found.",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "name": "security-report.txt",
        "status": "stored",
    }
    assert stored["security-report.txt"] == "No critical vulnerabilities found."


def test_list_artifacts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.main.list_artifacts",
        lambda: ["security-report.txt", "scan-results.txt"],
    )

    response = client.get(
        "/artifacts",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    assert response.json() == {
        "artifacts": ["security-report.txt", "scan-results.txt"]
    }


def test_reject_invalid_artifact_name() -> None:
    response = client.post(
        "/artifacts",
        headers=AUTH_HEADERS,
        json={
            "name": "../secret.txt",
            "content": "invalid",
        },
    )

    assert response.status_code == 422


def test_storage_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(name: str, content: str) -> None:
        raise EndpointConnectionError(endpoint_url="http://localhost:4566")

    monkeypatch.setattr("app.main.upload_artifact", unavailable)

    response = client.post(
        "/artifacts",
        headers=AUTH_HEADERS,
        json={
            "name": "report.txt",
            "content": "test",
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Storage service unavailable"}


def test_reject_missing_api_key() -> None:
    response = client.get("/artifacts")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}


def test_reject_incorrect_api_key() -> None:
    response = client.get(
        "/artifacts",
        headers={"X-API-Key": "incorrect-key"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}


def test_authentication_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("API_KEY", raising=False)

    response = client.get(
        "/artifacts",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "API authentication is not configured"
    }