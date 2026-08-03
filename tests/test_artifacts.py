from botocore.exceptions import EndpointConnectionError
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_artifact(monkeypatch) -> None:
    stored: dict[str, str] = {}

    def fake_upload(name: str, content: str) -> None:
        stored[name] = content

    monkeypatch.setattr("app.main.upload_artifact", fake_upload)

    response = client.post(
        "/artifacts",
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


def test_list_artifacts(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.main.list_artifacts",
        lambda: ["security-report.txt", "scan-results.txt"],
    )

    response = client.get("/artifacts")

    assert response.status_code == 200
    assert response.json() == {
        "artifacts": ["security-report.txt", "scan-results.txt"]
    }


def test_reject_invalid_artifact_name() -> None:
    response = client.post(
        "/artifacts",
        json={
            "name": "../secret.txt",
            "content": "invalid",
        },
    )

    assert response.status_code == 422


def test_storage_unavailable(monkeypatch) -> None:
    def unavailable(name: str, content: str) -> None:
        raise EndpointConnectionError(endpoint_url="http://localhost:4566")

    monkeypatch.setattr("app.main.upload_artifact", unavailable)

    response = client.post(
        "/artifacts",
        json={
            "name": "report.txt",
            "content": "test",
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Storage service unavailable"}