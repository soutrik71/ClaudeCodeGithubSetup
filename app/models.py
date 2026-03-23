"""Shared Pydantic models used across routers."""
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Item models
# ---------------------------------------------------------------------------

class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Hammer"])
    description: Optional[str] = Field(None, max_length=300)
    price: float = Field(..., gt=0, examples=[9.99])
    in_stock: bool = True


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    price: Optional[float] = Field(None, gt=0)
    in_stock: Optional[bool] = None


class ItemResponse(ItemBase):
    id: int


# ---------------------------------------------------------------------------
# User models
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["alice"])
    email: str = Field(..., examples=["alice@example.com"])


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserResponse(UserBase):
    id: int
    is_active: bool = True


# ---------------------------------------------------------------------------
# Product models
# ---------------------------------------------------------------------------

class ProductBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=150, examples=["Laptop"])
    category: str = Field(..., examples=["electronics"])
    price: float = Field(..., gt=0, examples=[999.99])


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    tags: list[str] = []
