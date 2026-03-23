# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Template repository demonstrating how to integrate Claude Code with GitHub, using a FastAPI showcase app as the example codebase. Two integrations are provided: an interactive `@claude` responder and an automated pytest generator that runs on every PR.

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

# Run tests with verbose output and short tracebacks
pytest tests/ -v --tb=short
```

## Architecture

**Stack:** FastAPI ~0.110 + Pydantic v2 ~2.6 + pytest ~8.0 + httpx ~0.27 (async test client) + pytest-asyncio ~0.23

The app (`app/`) follows a three-layer structure:

- `main.py` — FastAPI app init, health-check routes (`GET /`, `GET /ping`), router registration
- `models.py` — Pydantic `BaseModel` classes shared across routers: `ItemBase/Create/Update/Response`, `UserBase/Create/Response`, `ProductBase/Create/Response`
- `dependencies.py` — Reusable `Depends()` callables:
  - `get_api_key` — reads `X-Api-Key` header; raises 403 if value is present but not `"secret"`
  - `pagination` — `skip` (≥0) and `limit` (1–100) query params, returns `{"skip": int, "limit": int}`
- `routers/` — Three `APIRouter` modules, each owning its own module-level `store = _Store()` instance:
  - `items.py` — prefix `/items`: full CRUD, `GET /search`, pagination via `Depends(pagination)`
  - `users.py` — prefix `/users`: create (API-key guard via `dependencies=[Depends(get_api_key)]`), nested `GET /{user_id}/items`
  - `products.py` — prefix `/products`: background tasks on create, `GET /category/{category}` with `VALID_CATEGORIES` check; invalid category raises `HTTP_422_UNPROCESSABLE_ENTITY` (not `_CONTENT` — that constant doesn't exist in starlette ~0.36)

### In-memory stores

Each router declares a private `_Store` class with `.db` (dict), `._next_id` (int), and `.reset()`. The module-level instance is named `store`. To reset between tests:

```python
from app.routers import items, users, products

@pytest.fixture(autouse=True)
def reset_stores():
    items.store.reset()
    users.store.reset()
    products.store.reset()
    yield
```

### FastAPI TestClient pattern

```python
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    yield TestClient(app)
```

### Dependency override pattern (API-key guard)

```python
from app.dependencies import get_api_key

@pytest.fixture
def authed_client():
    app.dependency_overrides[get_api_key] = lambda: "secret"
    yield TestClient(app)
    app.dependency_overrides.clear()
```

## GitHub Actions / Claude Code Integration

`.github/workflows/code-test.yml` defines two jobs:

### Job 1 — Claude Interactive

Triggers when `@claude` appears in an issue body, issue comment, PR review, or PR review comment. Claude responds directly in the thread. Requires `ANTHROPIC_API_KEY` repository secret.

### Workflow-level env

`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` — opts all actions into Node.js 24 now (Node 20 is deprecated; GitHub forces Node 24 by default from June 2026).

### Job 2 — Claude Test Generator

Triggers on every `pull_request` event. Three-step pipeline:

1. **Claude writes tests** (`claude-code-action@v1` with `Read,Write,Edit,Glob` tools, max 20 turns) — explores source, plans, writes pytest files under `tests/`; does NOT run pytest
2. **Runner executes pytest** — real exit code propagates to job status (used by branch protection)
3. **Artifact upload** — `test-report/pytest-report.txt` retained for 14 days; uploads even on failure

## Critical Rule — Workflow File and PRs

`anthropics/claude-code-action@v1` performs OIDC-based security validation on every run: it exchanges a GitHub OIDC token with Anthropic's backend, which checks that `.github/workflows/code-test.yml` on the PR branch is **byte-for-byte identical** to the version on `main`.

**If the workflow file differs from `main`, the action fails with 401 on all attempts. No code change in the workflow can bypass this — it is server-side validation.**

### Rules

- **Never modify `.github/workflows/code-test.yml` in a feature PR** — it will break the action for that PR
- Workflow changes must be pushed directly to `main` or merged via a dedicated workflow-only PR (the action will skip on that PR by design; that is expected)
- After merging workflow changes to `main`, all subsequent feature PRs will use the updated workflow

### One-time bootstrap

When first adding this workflow to a new repo, the file won't exist on `main` yet. Merge it once before opening feature PRs:

```bash
git checkout main
git merge develop --no-ff -m "bootstrap: add Claude Code workflow"
git push origin main
```

## Branch protection setup (to gate merges on tests)

1. GitHub → **Settings → Branches → Add branch protection rule**
2. Pattern: `main`
3. Enable **"Require status checks to pass before merging"**
4. Add required check: `Claude — Generate Tests / Run pytest & upload report`
