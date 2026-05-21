import hashlib
import os
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)  # format: salt$hash
    address = Column(Text, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")

    # ---------- Password helpers ----------

    @staticmethod
    def _hash(plain: str, salt: str) -> str:
        """Hash password với PBKDF2-HMAC-SHA256 + salt."""
        dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 260_000)
        return dk.hex()

    def set_password(self, plain: str) -> None:
        """Tạo salt ngẫu nhiên, hash và lưu dạng 'salt$hash'."""
        salt = os.urandom(16).hex()
        self.password_hash = f"{salt}${self._hash(plain, salt)}"

    def verify_password(self, plain: str) -> bool:
        """Xác thực mật khẩu — hỗ trợ cả hash cũ (SHA-256 thuần) để migration."""
        if "$" in self.password_hash:
            # Hash mới: salt$hash
            salt, stored_hash = self.password_hash.split("$", 1)
            return self._hash(plain, salt) == stored_hash
        else:
            # Hash cũ (SHA-256 thuần): tự động nâng cấp khi đăng nhập thành công
            old_hash = hashlib.sha256(plain.encode()).hexdigest()
            if self.password_hash == old_hash:
                self.set_password(plain)  # nâng cấp lên hash mới
                return True
            return False

    def __repr__(self):
        return f"<User id={self.id} email='{self.email}' is_admin={self.is_admin}>"
