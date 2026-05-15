from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    # Relationships
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

    @property
    def subtotal(self):
        """Return line-item subtotal in VND."""
        return self.product.price * self.quantity

    @property
    def formatted_subtotal(self):
        return f"{self.subtotal:,}₫".replace(",", ".")

    def __repr__(self):
        return f"<CartItem id={self.id} user_id={self.user_id} product_id={self.product_id} qty={self.quantity}>"
