from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import relationship

from app.database.database import Base


class ProductAttribute(Base):
    __tablename__ = "product_attributes"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        unique=True,
        nullable=False
    )

    color = Column(String(100))

    material = Column(String(100))

    style = Column(String(100))

    shape = Column(String(100))

    product = relationship(
        "Product",
        back_populates="attributes"
    )