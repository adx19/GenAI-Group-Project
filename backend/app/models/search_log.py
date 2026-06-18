from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import relationship


from app.database.database import Base
from app.models.enums import SearchType


class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)

    query = Column(String(500))

    search_type = Column(
        Enum(SearchType),
        nullable=False
    )

    results_count = Column(
        Integer,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    clicks = relationship(
        "SearchClick",
        back_populates="search_log"
    )
