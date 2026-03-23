# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Template repository demonstrating how to integrate Claude Code with GitHub, using a FastAPI showcase app as the example codebase.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
uvicorn app.main:app --reload

# Run tests
pytest

# Run a single test file
pytest tests/test_items.py

# Run a single test
pytest tests/test_items.py::test_create_item
```

## Architecture

**Stack:** FastAPI + Pydantic v2 + pytest + httpx (for async test client)

The app (`app/`) follows a three-layer structure:

- `main.py` — FastAPI app init, health-check routes, router registration
- `models.py` — Pydantic `BaseModel` classes shared across routers (Item, User, Product)
- `dependencies.py` — Reusable `Depends()` callables: `get_api_key` (header guard) and `pagination` (skip/limit query params)
- `routers/` — Three `APIRouter` modules, each owning its own in-memory `_Store`:
  - `items.py` — CRUD with pagination, search, path/query params
  - `users.py` — Dependency injection, nested resources, API key guard
  - `products.py` — Response models, background tasks, category filtering, path validation

Each router is self-contained: models live in `app/models.py`, storage is a module-level dict/list instance inside the router file, and the router is mounted in `main.py` via `app.include_router(...)`.

## GitHub Actions / Claude Code Integration

`.github/workflows/code-test.yml` runs `anthropics/claude-code-action@v1` and triggers when any comment, PR review, or new issue contains `@claude`. The action requires an `ANTHROPIC_API_KEY` repository secret.
