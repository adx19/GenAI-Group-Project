from sqlalchemy import Column, Integer, String, Text, Float, Boolean
from sqlalchemy.orm import relationship
from app.database.database import Base

class Product(Base):
  __tablename__ = "products"

  id = Column(Integer, primary_key=True, index=True)
  asin = Column(String(50), unique=True, nullable=False)
  name = Column(String(500), nullable=False)
  category = Column(String(255), nullable=False)
  description = Column(Text)
  image_url = Column(Text)
  price = Column(Float)
  rating = Column(Float)
  is_best_seller = Column(Boolean, default=False)

  attributes = relationship(
    "ProductAttribute",
    back_populates="product",
    uselist = False,
    cascade="all, delete-orphan"
  )

  clicks = relationship("SearchClick", back_populates="product")