"""Reusable FastAPI dependencies."""
from typing import Annotated
from fastapi import Header, HTTPException, Query


def get_api_key(x_api_key: Annotated[str | None, Header()] = None) -> str | None:
    """Simple header-based API-key guard (illustrative — not production-ready)."""
    if x_api_key is not None and x_api_key != "secret":
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


def pagination(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    """Common pagination query parameters."""
    return {"skip": skip, "limit": limit}
