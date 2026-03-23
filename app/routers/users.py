"""Users router — demonstrates dependency injection and nested routes.

Route patterns shown:
- GET  /users/              list users (dependency injection for pagination)
- POST /users/              create user (body + dependency guard)
- GET  /users/{user_id}     get user by ID (path param)
- GET  /users/{user_id}/items  get all items belonging to a user (nested resource)
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_api_key, pagination
from app.models import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


class _Store:
    """In-memory store for demonstration purposes."""

    def __init__(self) -> None:
        self.db: dict[int, dict] = {}
        self.user_items: dict[int, list[str]] = {}
        self._next_id: int = 1

    def next_id(self) -> int:
        current = self._next_id
        self._next_id += 1
        return current

    def reset(self) -> None:
        self.db.clear()
        self.user_items.clear()
        self._next_id = 1


store = _Store()


def _get_user_or_404(user_id: int) -> dict:
    if user_id not in store.db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return store.db[user_id]


# ---------------------------------------------------------------------------
# List (dependency injection for pagination)
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[UserResponse], summary="List users")
def list_users(paging: Annotated[dict, Depends(pagination)]):
    """Return a paginated list of users."""
    users = list(store.db.values())
    return users[paging["skip"] : paging["skip"] + paging["limit"]]


# ---------------------------------------------------------------------------
# Create (request body + optional API-key header dependency)
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
    dependencies=[Depends(get_api_key)],
)
def create_user(user: UserCreate):
    """Create a new user.  Requires ``X-Api-Key: secret`` header when provided."""
    user_id = store.next_id()
    record = {"id": user_id, "username": user.username, "email": user.email, "is_active": True}
    store.db[user_id] = record
    store.user_items[user_id] = []
    return record


# ---------------------------------------------------------------------------
# Fetch single user (path parameter)
# ---------------------------------------------------------------------------

@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID")
def get_user(user_id: int):
    """Return a single user by ID."""
    return _get_user_or_404(user_id)


# ---------------------------------------------------------------------------
# Nested resource: items owned by a user
# ---------------------------------------------------------------------------

@router.get("/{user_id}/items", response_model=list[str], summary="Get items for a user")
def get_user_items(user_id: int):
    """Return the list of item names associated with the given user."""
    _get_user_or_404(user_id)
    return store.user_items.get(user_id, [])
