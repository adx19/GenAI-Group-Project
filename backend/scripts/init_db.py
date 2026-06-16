from app.database.database import Base
from app.database.session import engine

from app.models.product import Product
from app.models.product_attribute import ProductAttribute
from app.models.search_log import SearchLog
from app.models.search_click import SearchClick

Base.metadata.create_all(bind=engine)

print("Database tables created.")