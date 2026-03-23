"""Products router — demonstrates response models, background tasks, and enum path params.

Route patterns shown:
- GET  /products/                    list products
- POST /products/                    create product (body + background task)
- GET  /products/{product_id}        fetch product (path param)
- GET  /products/category/{category} filter by enum-like category (path param)
"""
import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, status

from app.dependencies import pagination
from app.models import ProductCreate, ProductResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["products"])


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

VALID_CATEGORIES = {"electronics", "clothing", "food", "books", "sports"}


def _get_product_or_404(product_id: int) -> dict:
    if product_id not in store.db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return store.db[product_id]


def _log_new_product(product_id: int, title: str) -> None:
    """Background task: simulate async side-effect (e.g. send notification)."""
    logger.info("New product created: id=%d title=%s", product_id, title)


# ---------------------------------------------------------------------------
# List (pagination dependency)
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[ProductResponse], summary="List products")
def list_products(paging: Annotated[dict, Depends(pagination)]):
    """Return a paginated list of products."""
    products = list(store.db.values())
    return products[paging["skip"] : paging["skip"] + paging["limit"]]


# ---------------------------------------------------------------------------
# Filter by category (path parameter with validation)
# ---------------------------------------------------------------------------

@router.get("/category/{category}", response_model=list[ProductResponse], summary="Filter by category")
def list_by_category(
    category: Annotated[str, Path(description="Product category name")],
):
    """Return all products in the given category."""
    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown category '{category}'. Valid categories: {sorted(VALID_CATEGORIES)}",
        )
    return [p for p in store.db.values() if p["category"] == category]


# ---------------------------------------------------------------------------
# Fetch single product (path parameter)
# ---------------------------------------------------------------------------

@router.get("/{product_id}", response_model=ProductResponse, summary="Get product by ID")
def get_product(product_id: int):
    """Return a single product by ID."""
    return _get_product_or_404(product_id)


# ---------------------------------------------------------------------------
# Create (request body + background task)
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
)
def create_product(product: ProductCreate, background_tasks: BackgroundTasks):
    """Create a new product.  Fires a background task after returning the response."""
    product_id = store.next_id()
    record = {"id": product_id, **product.model_dump(), "tags": []}
    store.db[product_id] = record
    background_tasks.add_task(_log_new_product, product_id, product.title)
    return record
