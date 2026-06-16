from fastapi import APIRouter
from app.database.session import SessionLocal
from app.models.search_log import SearchLog
from app.models.search_click import SearchClick
from app.models.enums import SearchType
from app.services.analytics.search_tracking_service import(SearchTrackingService)

router = APIRouter(
  prefix = "/analytics",
  tags = ["Analytics"]
)


tracker = SearchTrackingService()

@router.post("/click")
def track_click(search_log_id: int, product_id:int):
  
  click_id = tracker.log_click(
      search_log_id=search_log_id,
      product_id=product_id
  )

  return {
      "click_id": click_id,
      "message": "Click tracked"
  }

@router.get("/top-clicked")
def get_top_clicked():
  results = tracker.get_most_clicked_products()
  
  return [
    {
      "id": product.id,
      "name" : product.name,
      "category" : product.category,
      "click_count" : click_count
    }
    
    for product, click_count in results
  ]
  
@router.get("/")
def get_analytics():

    db = SessionLocal()

    try:

        total_searches = (
            db.query(SearchLog)
            .count()
        )

        text_searches = (
            db.query(SearchLog)
            .filter(
                SearchLog.search_type == SearchType.TEXT
            )
            .count()
        )

        image_searches = (
            db.query(SearchLog)
            .filter(
                SearchLog.search_type == SearchType.IMAGE
            )
            .count()
        )

        multimodal_searches = (
            db.query(SearchLog)
            .filter(
                SearchLog.search_type == SearchType.MULTIMODAL
            )
            .count()
        )

        total_clicks = (
            db.query(SearchClick)
            .count()
        )

        zero_result_searches = (
            db.query(SearchLog)
            .filter(
                SearchLog.results_count == 0
            )
            .count()
        )

        ctr = (
            total_clicks / total_searches
            if total_searches > 0
            else 0
        )

        abandonment_rate = (
            (
                total_searches - total_clicks
            ) / total_searches
            if total_searches > 0
            else 0
        )

        return {
            "total_searches": total_searches,
            "text_searches": text_searches,
            "image_searches": image_searches,
            "multimodal_searches": multimodal_searches,
            "ctr": round(ctr, 2),
            "abandonment_rate": round(abandonment_rate, 2),
            "zero_result_searches": zero_result_searches
        }

    finally:
        db.close()