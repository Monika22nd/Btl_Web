# models/__init__.py
# Import all models so SQLAlchemy can discover them when Base.metadata.create_all() is called.

from .category import Category
from .brand import Brand
from .product import Product, ProductSpec
from .user import User
from .cart import CartItem
from .order import Order, OrderItem

__all__ = [
    "Category",
    "Brand",
    "Product",
    "ProductSpec",
    "User",
    "CartItem",
    "Order",
    "OrderItem",
]
