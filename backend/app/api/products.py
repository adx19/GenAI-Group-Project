from app.database import database
from fastapi import APIRouter
from fastapi import HTTPException
from app.models.product_attribute import ProductAttribute
from app.database.session import SessionLocal
from app.models.product import Product

router = APIRouter(
  prefix="/products",
  tags=["Products"]
)

@router.get("/{product_id}")
def get_product(product_id: int):
  
  db = SessionLocal()
  
  try:
    
    product = (db.query(Product).filter(Product.id == product_id).first())
    
    attributes = (db.query(ProductAttribute).filter(ProductAttribute.product_id == product_id).first())
    
    if not product:
      
      raise HTTPException(
        status_code=404,
        detail = "Product not found"
      )
      
    return {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "description": product.description,
        "price": product.price,
        "rating": product.rating,
        "image_url": product.image_url,
        "attributes": {
            "color": (
                attributes.color
                if attributes
                else None
            ),
            "material": (
                attributes.material
                if attributes
                else None
            ),
            "style": (
                attributes.style
                if attributes
                else None
            ),
            "shape": (
                attributes.shape
                if attributes
                else None
            )
        }
    }
  finally:
    db.close()