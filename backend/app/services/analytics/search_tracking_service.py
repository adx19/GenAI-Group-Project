from app.database.session import SessionLocal
from sqlalchemy import func
from app.models.product import Product

from app.models.search_log import SearchLog
from app.models.search_click import SearchClick

class SearchTrackingService:
  
  def log_search(self, query, search_type, results_count):
    
    db = SessionLocal()
    
    try:
      search_log = SearchLog(query=query, search_type=search_type, results_count=results_count)
      
      db.add(search_log)
      
      db.commit()
      
      db.refresh(search_log)
      return search_log.id
    finally:
      db.close()
  def log_click(self, search_log_id, product_id):
    
    db = SessionLocal()
    
    try:
      
      click = SearchClick(search_log_id=search_log_id, product_id=product_id)
      
      db.add(click)
      
      db.commit()
      db.refresh(click)
      
      return click.id
    finally:
      
      db.close()
  def get_most_clicked_products(self, limit: int = 10):
    
    db = SessionLocal()
    
    try:
      
      results = (db.query(Product, func.count(SearchClick.id).label("click_count")).join(SearchClick, Product.id == SearchClick.product_id).group_by(Product.id).order_by(func.count(SearchClick.id).desc()).limit(limit).all())
      
      return results
    finally:
      
      db.close()
       