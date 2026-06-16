from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import relationship

from app.database.database import Base


class SearchClick(Base):
    __tablename__ = "search_clicks"

    id = Column(Integer, primary_key=True, index=True)

    search_log_id = Column(
        Integer,
        ForeignKey("search_logs.id"),
        nullable=False
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    clicked_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    search_log = relationship(
        "SearchLog",
        back_populates="clicks"
    )

    product = relationship(
        "Product",
        back_populates="clicks"
    )