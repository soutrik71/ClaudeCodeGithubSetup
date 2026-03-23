"""Items router — demonstrates CRUD with path params, query params, and request body.

Route patterns shown:
- GET  /items/          list with pagination (query params)
- POST /items/          create (request body)
- GET  /items/{item_id} fetch single item (path param)
- PUT  /items/{item_id} full/partial update (path param + request body)
- DELETE /items/{item_id} delete (path param)
- GET  /items/search    filter by name (query param)
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import pagination
from app.models import ItemCreate, ItemResponse, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])


class _Store:
    """In-memory store for demonstration purposes."""

    def __init__(self) -> None:
        self.db: dict[int, dict] = {}
        self._next_id: int = 1

    def next_id(self) -> int:
        current = self._next_id
        self._next_id += 1
        return current

    def reset(self) -> None:
        self.db.clear()
        self._next_id = 1


store = _Store()


def _get_item_or_404(item_id: int) -> dict:
    if item_id not in store.db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return store.db[item_id]


# ---------------------------------------------------------------------------
# List with pagination (query parameters via dependency)
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[ItemResponse], summary="List items")
def list_items(paging: Annotated[dict, Depends(pagination)]):
    """Return a paginated list of all items."""
    items = list(store.db.values())
    return items[paging["skip"] : paging["skip"] + paging["limit"]]


# ---------------------------------------------------------------------------
# Search by name (query parameter)
# ---------------------------------------------------------------------------

@router.get("/search", response_model=list[ItemResponse], summary="Search items by name")
def search_items(name: Annotated[str, Query(min_length=1)] = ""):
    """Filter items whose name contains the given substring (case-insensitive)."""
    return [i for i in store.db.values() if name.lower() in i["name"].lower()]


# ---------------------------------------------------------------------------
# Fetch single item (path parameter)
# ---------------------------------------------------------------------------

@router.get("/{item_id}", response_model=ItemResponse, summary="Get item by ID")
def get_item(item_id: int):
    """Return a single item by its integer ID."""
    return _get_item_or_404(item_id)


# ---------------------------------------------------------------------------
# Create (request body with Pydantic model)
# ---------------------------------------------------------------------------

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED, summary="Create item")
def create_item(item: ItemCreate):
    """Create a new item from the request body."""
    item_id = store.next_id()
    record = {"id": item_id, **item.model_dump()}
    store.db[item_id] = record
    return record


# ---------------------------------------------------------------------------
# Full / partial update (path param + optional body fields)
# ---------------------------------------------------------------------------

@router.put("/{item_id}", response_model=ItemResponse, summary="Update item")
def update_item(item_id: int, item: ItemUpdate):
    """Update only the provided fields of an existing item."""
    record = _get_item_or_404(item_id)
    updates = item.model_dump(exclude_unset=True)
    record.update(updates)
    return record


# ---------------------------------------------------------------------------
# Delete (path parameter, 204 No Content)
# ---------------------------------------------------------------------------

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete item")
def delete_item(item_id: int):
    """Remove an item by ID."""
    _get_item_or_404(item_id)
    del store.db[item_id]
