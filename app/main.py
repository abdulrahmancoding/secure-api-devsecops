from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, HTTPException, Security
from pydantic import BaseModel, Field

from app.security import require_api_key
from app.storage import list_artifacts, upload_artifact


app = FastAPI(
    title="Secure API",
    description="A containerized API for learning DevSecOps practices.",
    version="0.3.0",
)


class ArtifactCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9._-]+$",
    )
    content: str = Field(min_length=1, max_length=10_000)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.post(
    "/artifacts",
    status_code=201,
    dependencies=[Security(require_api_key)],
)
def create_artifact(artifact: ArtifactCreate) -> dict[str, str]:
    try:
        upload_artifact(artifact.name, artifact.content)
    except (BotoCoreError, ClientError) as error:
        raise HTTPException(
            status_code=503,
            detail="Storage service unavailable",
        ) from error

    return {
        "name": artifact.name,
        "status": "stored",
    }


@app.get(
    "/artifacts",
    dependencies=[Security(require_api_key)],
)
def get_artifacts() -> dict[str, list[str]]:
    try:
        names = list_artifacts()
    except (BotoCoreError, ClientError) as error:
        raise HTTPException(
            status_code=503,
            detail="Storage service unavailable",
        ) from error

    return {"artifacts": names}