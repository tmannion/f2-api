"""
Simple API key authentication for write endpoints.

The API key is read from the F2_API_KEY environment variable.
Clients pass it via the X-API-Key header on POST requests.
"""

import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY = os.environ.get("F2_API_KEY", "")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str | None = Security(api_key_header)) -> str:
    """Dependency that validates the API key. Add to POST endpoints."""
    if not API_KEY:
        raise HTTPException(
            status_code=500, detail="Server misconfigured: F2_API_KEY not set"
        )
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return key
