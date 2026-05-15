import hashlib
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)          # Vietnamese full name
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)               # Vietnamese phone number
    password_hash = Column(String, nullable=False)      # Hashed via hashlib
    address = Column(Text, nullable=True)               # Delivery address
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")

    # ---------- Password helpers ----------

    @staticmethod
    def hash_password(plain: str) -> str:
        """Hash a plain-text password using SHA-256."""
        return hashlib.sha256(plain.encode()).hexdigest()

    def set_password(self, plain: str) -> None:
        """Hash and store the password."""
        self.password_hash = self.hash_password(plain)

    def verify_password(self, plain: str) -> bool:
        """Return True if the plain-text password matches the stored hash."""
        return self.password_hash == self.hash_password(plain)

    def __repr__(self):
        return f"<User id={self.id} email='{self.email}' is_admin={self.is_admin}>"
