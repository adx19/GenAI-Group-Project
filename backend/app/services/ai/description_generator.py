import google.generativeai as genai

from app.core.config import settings

class DescriptionGenerator:
  
  def __init__(self):
    
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    self.model = (genai.GenerativeModel("gemini-2.5-flash"))
    
  def generate(self, product_name: str, category: str, attribute: dict):
    prompt = f"""
    Generate a professional ecommerce product description.
    
    Product Name:
    {product_name}
    
    Attributes:
    {category}
    
    Requirements:
    - 3 to 5 sentences
    - Professional tone
    - Mention important attributes
    - Do not invent specifications
    - Suitable for an online marketplace
    
    Return only the description
    """
    
    response = (self.model.generate_content(prompt))
    
    return response.text.strip()