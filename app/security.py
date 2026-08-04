import os
from secrets import compare_digest
from typing import Annotated

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader


api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


def require_api_key(
    provided_api_key: Annotated[str | None, Security(api_key_header)],
) -> None:
    expected_api_key = os.getenv("API_KEY")

    if not expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured",
        )

    if provided_api_key is None or not compare_digest(
        provided_api_key,
        expected_api_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )