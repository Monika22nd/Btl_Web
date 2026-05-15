from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)               # e.g. "iPhone 16 Pro Max 256GB"
    slug = Column(String, unique=True, nullable=False)  # URL-safe name
    description = Column(Text, nullable=True)           # Full description
    price = Column(Integer, nullable=False)             # Price in VND (no decimals)
    original_price = Column(Integer, nullable=True)     # Strike-through price (for discounts)
    image_url = Column(String, nullable=True)           # Main product image path/URL
    stock = Column(Integer, default=0)                  # Available quantity
    rating = Column(Float, default=0.0)                 # Average rating (1–5)
    review_count = Column(Integer, default=0)           # Number of reviews
    is_featured = Column(Boolean, default=False)        # Show on homepage

    created_at = Column(DateTime, default=datetime.utcnow)

    # Foreign keys
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)

    # Relationships
    category = relationship("Category", back_populates="products")
    brand = relationship("Brand", back_populates="products")
    specs = relationship("ProductSpec", back_populates="product", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

    @property
    def discount_percent(self):
        """Calculate discount percentage if original_price exists."""
        if self.original_price and self.original_price > self.price:
            return round((1 - self.price / self.original_price) * 100)
        return 0

    @property
    def formatted_price(self):
        """Return price formatted as Vietnamese currency string."""
        return f"{self.price:,}₫".replace(",", ".")

    @property
    def formatted_original_price(self):
        if self.original_price:
            return f"{self.original_price:,}₫".replace(",", ".")
        return None

    def __repr__(self):
        return f"<Product id={self.id} name='{self.name}' price={self.price}>"


class ProductSpec(Base):
    __tablename__ = "product_specs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    spec_name = Column(String, nullable=False)   # e.g. "Màn hình", "RAM", "Pin"
    spec_value = Column(String, nullable=False)  # e.g. "6.7 inch OLED", "8GB", "4500mAh"

    # Relationship
    product = relationship("Product", back_populates="specs")

    def __repr__(self):
        return f"<ProductSpec product_id={self.product_id} {self.spec_name}={self.spec_value}>"
