import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage import BUCKET_NAME, get_s3_client


client = TestClient(app)


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Integration tests require LocalStack and Terraform infrastructure",
)
def test_artifact_storage_with_localstack() -> None:
    artifact_name = f"integration-{uuid4().hex}.txt"
    artifact_content = "Integration test successfully reached encrypted S3."

    s3_client = get_s3_client()

    try:
        upload_response = client.post(
            "/artifacts",
            json={
                "name": artifact_name,
                "content": artifact_content,
            },
        )

        assert upload_response.status_code == 201
        assert upload_response.json() == {
            "name": artifact_name,
            "status": "stored",
        }

        list_response = client.get("/artifacts")

        assert list_response.status_code == 200
        assert artifact_name in list_response.json()["artifacts"]

        stored_object = s3_client.get_object(
            Bucket=BUCKET_NAME,
            Key=artifact_name,
        )

        stored_content = stored_object["Body"].read().decode("utf-8")

        assert stored_content == artifact_content
        assert stored_object["ServerSideEncryption"] == "aws:kms"
        assert stored_object["SSEKMSKeyId"]

    finally:
        s3_client.delete_object(
            Bucket=BUCKET_NAME,
            Key=artifact_name,
        )