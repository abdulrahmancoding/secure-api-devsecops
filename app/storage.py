import os
from typing import Any

import boto3
from botocore.config import Config


BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "secure-api-artifacts-local")
S3_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


def get_s3_client() -> Any:
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        region_name=AWS_REGION,
        config=Config(s3={"addressing_style": "path"}),
    )


def upload_artifact(name: str, content: str) -> None:
    get_s3_client().put_object(
        Bucket=BUCKET_NAME,
        Key=name,
        Body=content.encode("utf-8"),
        ContentType="text/plain",
    )


def list_artifacts() -> list[str]:
    response = get_s3_client().list_objects_v2(Bucket=BUCKET_NAME)
    return [item["Key"] for item in response.get("Contents", [])]