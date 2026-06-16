from sqlalchemy import func

from app.database.session import SessionLocal
from app.models.search_log import SearchLog
from app.models.search_click import SearchClick
from app.models.product import Product

class SearchAnalyticsService:
  
  def get_popular_searches(self, limit=10):
    db = SessionLocal()
    
    try:
      
      return (db.query(SearchLog.query, func.count(SearchLog.id).label("count")).group_by(SearchLog.query).order_by(func.count(SearchLog.id)).limit(limit).all())
    finally:
      
      db.close()
  def get_most_clicked_products(self, limit=10):
    db = SessionLocal()
    
    try:
      
      return (db.query(Product.name, func.count(SearchClick.id).label("clicks")).join(SearchClick, Product.id == SearchClick.product_id).group_by(Product.id).order_by(func.count(SearchClick.id).desc().limit(limit).all()))
    finally:
      
      db.close()


