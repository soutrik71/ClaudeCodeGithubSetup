"""FastAPI application entry point.

Showcases different ways to create API routes:

1. **Direct route** on the app object (``@app.get``)
2. **APIRouter** — items router (CRUD, path params, query params, request body)
3. **APIRouter** — users router (dependency injection, nested resources)
4. **APIRouter** — products router (response models, background tasks, path validation)
"""
from fastapi import FastAPI

from app.routers import items, products, users

app = FastAPI(
    title="FastAPI Routes Showcase",
    description=(
        "Demonstrates different ways to define API routes with FastAPI: "
        "direct decorators, APIRouter grouping, path/query parameters, "
        "request bodies, response models, dependency injection, and background tasks."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# 1. Direct route on the app object — simplest possible approach
# ---------------------------------------------------------------------------

@app.get("/", tags=["root"], summary="Health check")
def root():
    """Return a simple health-check message."""
    return {"message": "FastAPI Routes Showcase is running!"}


@app.get("/ping", tags=["root"], summary="Ping")
def ping():
    """Lightweight liveness probe."""
    return {"ping": "pong"}


# ---------------------------------------------------------------------------
# 2-4. Include APIRouter instances (modular approach)
# ---------------------------------------------------------------------------

app.include_router(items.router)
app.include_router(users.router)
app.include_router(products.router)
