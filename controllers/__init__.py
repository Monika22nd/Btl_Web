# controllers/__init__.py
from .home_controller import router as home_router
from .product_controller import router as product_router
from .cart_controller import router as cart_router
from .order_controller import router as order_router
from .auth_controller import router as auth_router
from .admin_controller import router as admin_router

__all__ = [
    "home_router",
    "product_router",
    "cart_router",
    "order_router",
    "auth_router",
    "admin_router",
]
