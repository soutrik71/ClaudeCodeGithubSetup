"""Tests for the FastAPI Routes Showcase application.

Covers:
- Root / ping endpoints (direct app decorator)
- Items router: CRUD, path params, query params, request body, pagination, search
- Users router: create, list, get, nested resource, dependency injection
- Products router: create, list, get, category filter, background task
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import items as items_router
from app.routers import products as products_router
from app.routers import users as users_router


@pytest.fixture(autouse=True)
def reset_dbs():
    """Reset all in-memory stores before each test for isolation."""
    items_router.store.reset()
    users_router.store.reset()
    products_router.store.reset()
    yield


client = TestClient(app)


# ===========================================================================
# Root / ping
# ===========================================================================

class TestRoot:
    def test_root(self):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json() == {"message": "FastAPI Routes Showcase is running!"}

    def test_ping(self):
        r = client.get("/ping")
        assert r.status_code == 200
        assert r.json() == {"ping": "pong"}


# ===========================================================================
# Items router
# ===========================================================================

class TestItemsCRUD:
    def _create(self, name="Hammer", price=9.99):
        return client.post("/items/", json={"name": name, "price": price})

    def test_create_item(self):
        r = self._create()
        assert r.status_code == 201
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "Hammer"
        assert data["price"] == 9.99
        assert data["in_stock"] is True

    def test_create_item_missing_field(self):
        r = client.post("/items/", json={"name": "Nails"})
        assert r.status_code == 422

    def test_get_item(self):
        self._create()
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["name"] == "Hammer"

    def test_get_item_not_found(self):
        r = client.get("/items/999")
        assert r.status_code == 404

    def test_list_items(self):
        self._create("A", 1.0)
        self._create("B", 2.0)
        r = client.get("/items/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_list_items_pagination(self):
        for i in range(5):
            self._create(f"Item{i}", float(i + 1))
        r = client.get("/items/?skip=2&limit=2")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 2
        assert items[0]["name"] == "Item2"

    def test_update_item(self):
        self._create()
        r = client.put("/items/1", json={"price": 19.99})
        assert r.status_code == 200
        assert r.json()["price"] == 19.99
        assert r.json()["name"] == "Hammer"  # unchanged

    def test_update_item_not_found(self):
        r = client.put("/items/999", json={"price": 1.0})
        assert r.status_code == 404

    def test_delete_item(self):
        self._create()
        r = client.delete("/items/1")
        assert r.status_code == 204
        assert client.get("/items/1").status_code == 404

    def test_delete_item_not_found(self):
        r = client.delete("/items/999")
        assert r.status_code == 404

    def test_search_items(self):
        self._create("Hammer", 9.99)
        self._create("Screwdriver", 4.99)
        r = client.get("/items/search?name=hammer")
        assert r.status_code == 200
        results = r.json()
        assert len(results) == 1
        assert results[0]["name"] == "Hammer"

    def test_search_items_no_match(self):
        self._create("Hammer", 9.99)
        r = client.get("/items/search?name=wrench")
        assert r.status_code == 200
        assert r.json() == []


# ===========================================================================
# Users router
# ===========================================================================

class TestUsers:
    def _create_user(self, username="alice", email="alice@example.com", api_key=None):
        headers = {"X-Api-Key": api_key} if api_key else {}
        return client.post(
            "/users/",
            json={"username": username, "email": email, "password": "secret123"},
            headers=headers,
        )

    def test_create_user(self):
        r = self._create_user()
        assert r.status_code == 201
        data = r.json()
        assert data["id"] == 1
        assert data["username"] == "alice"
        assert data["is_active"] is True

    def test_create_user_invalid_api_key(self):
        r = self._create_user(api_key="wrong")
        assert r.status_code == 403

    def test_create_user_valid_api_key(self):
        r = self._create_user(api_key="secret")
        assert r.status_code == 201

    def test_get_user(self):
        self._create_user()
        r = client.get("/users/1")
        assert r.status_code == 200
        assert r.json()["username"] == "alice"

    def test_get_user_not_found(self):
        r = client.get("/users/999")
        assert r.status_code == 404

    def test_list_users(self):
        self._create_user("alice", "a@example.com")
        self._create_user("bob", "b@example.com")
        r = client.get("/users/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_get_user_items(self):
        self._create_user()
        r = client.get("/users/1/items")
        assert r.status_code == 200
        assert r.json() == []

    def test_get_user_items_not_found(self):
        r = client.get("/users/999/items")
        assert r.status_code == 404


# ===========================================================================
# Products router
# ===========================================================================

class TestProducts:
    def _create_product(self, title="Laptop", category="electronics", price=999.99):
        return client.post("/products/", json={"title": title, "category": category, "price": price})

    def test_create_product(self):
        r = self._create_product()
        assert r.status_code == 201
        data = r.json()
        assert data["id"] == 1
        assert data["title"] == "Laptop"
        assert data["tags"] == []

    def test_create_product_missing_field(self):
        r = client.post("/products/", json={"title": "X", "price": 1.0})
        assert r.status_code == 422

    def test_get_product(self):
        self._create_product()
        r = client.get("/products/1")
        assert r.status_code == 200
        assert r.json()["title"] == "Laptop"

    def test_get_product_not_found(self):
        r = client.get("/products/999")
        assert r.status_code == 404

    def test_list_products(self):
        self._create_product("Laptop", "electronics", 999.99)
        self._create_product("T-Shirt", "clothing", 19.99)
        r = client.get("/products/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_list_by_category(self):
        self._create_product("Laptop", "electronics", 999.99)
        self._create_product("T-Shirt", "clothing", 19.99)
        r = client.get("/products/category/electronics")
        assert r.status_code == 200
        results = r.json()
        assert len(results) == 1
        assert results[0]["title"] == "Laptop"

    def test_list_by_invalid_category(self):
        r = client.get("/products/category/widgets")
        assert r.status_code == 422

    def test_list_by_category_empty(self):
        self._create_product("Laptop", "electronics", 999.99)
        r = client.get("/products/category/books")
        assert r.status_code == 200
        assert r.json() == []
