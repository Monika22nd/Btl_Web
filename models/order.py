from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


# Valid order status values
ORDER_STATUS = {
    "pending":   "Chờ xác nhận",
    "confirmed": "Đã xác nhận",
    "shipping":  "Đang giao hàng",
    "delivered": "Đã giao hàng",
    "cancelled": "Đã huỷ",
}


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total = Column(Integer, nullable=False)             # Total in VND
    status = Column(String, default="pending")          # See ORDER_STATUS above
    shipping_address = Column(Text, nullable=False)     # Delivery address
    phone = Column(String, nullable=False)              # Contact phone
    note = Column(Text, nullable=True)                  # Customer note
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    @property
    def status_label(self):
        """Return human-readable Vietnamese status label."""
        return ORDER_STATUS.get(self.status, self.status)

    @property
    def formatted_total(self):
        return f"{self.total:,}₫".replace(",", ".")

    def __repr__(self):
        return f"<Order id={self.id} user_id={self.user_id} total={self.total} status='{self.status}'>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)  # Price at time of order (snapshot)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    @property
    def subtotal(self):
        return self.price * self.quantity

    @property
    def formatted_price(self):
        return f"{self.price:,}₫".replace(",", ".")

    @property
    def formatted_subtotal(self):
        return f"{self.subtotal:,}₫".replace(",", ".")

    def __repr__(self):
        return f"<OrderItem id={self.id} order_id={self.order_id} product_id={self.product_id} qty={self.quantity}>"
