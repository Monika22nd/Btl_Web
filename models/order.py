from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

ORDER_STATUS = {
    "pending":   "Chờ xác nhận",
    "confirmed": "Đã xác nhận",
    "preparing": "Chuẩn bị hàng",
    "shipping":  "Đang giao hàng",
    "arrived":   "Đã giao tới nơi",
    "delivered": "Đã nhận hàng",
    "complaint": "Đang khiếu nại",
    "cancelled": "Đã huỷ",
}

# Trang thai admin duoc phep chuyen. delivered do khach xac nhan.
ADMIN_ALLOWED_STATUS = ["pending", "confirmed", "preparing", "shipping", "arrived", "cancelled"]


class Order(Base):
    __tablename__ = "orders"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=False)
    total            = Column(Integer, nullable=False)
    status           = Column(String, default="pending")
    recipient_name   = Column(String, nullable=True)    # Tên người nhận (mới thêm)
    shipping_address = Column(Text, nullable=False)
    phone            = Column(String, nullable=False)
    note             = Column(Text, nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)

    user  = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    @property
    def status_label(self):
        return ORDER_STATUS.get(self.status, self.status)

    @property
    def formatted_total(self):
        return f"{self.total:,}₫".replace(",", ".")

    def __repr__(self):
        return f"<Order id={self.id} status='{self.status}'>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id         = Column(Integer, primary_key=True, index=True)
    order_id   = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity   = Column(Integer, nullable=False)
    price      = Column(Integer, nullable=False)

    order   = relationship("Order", back_populates="items")
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
