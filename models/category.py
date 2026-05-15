from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)          # e.g. "Điện thoại", "Laptop"
    slug = Column(String, unique=True, nullable=False)  # e.g. "dien-thoai", "laptop"
    icon = Column(String, nullable=True)           # Emoji or icon class
    display_order = Column(Integer, default=0)     # For navbar ordering

    # Relationships
    products = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category id={self.id} name='{self.name}'>"
