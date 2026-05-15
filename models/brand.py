from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # e.g. "Apple", "Samsung"
    slug = Column(String, unique=True, nullable=False)  # e.g. "apple", "samsung"

    # Relationships
    products = relationship("Product", back_populates="brand")

    def __repr__(self):
        return f"<Brand id={self.id} name='{self.name}'>"
