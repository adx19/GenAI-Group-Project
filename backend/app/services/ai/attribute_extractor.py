import json
from PIL import Image

import google.generativeai as genai

from app.core.config import settings


class AttributeExtractor:

    def __init__(self):

        genai.configure(
            api_key=settings.GEMINI_API_KEY
        )

        self.model = genai.GenerativeModel(
            "gemini-3-flash-preview"
        )

    def extract_attributes(
        self,
        image_path: str
    ):

        image = Image.open(image_path)

        prompt = """
Analyze this product image.

Extract:

1. color
2. material
3. style
4. shape

Return ONLY valid JSON.

Example:

{
  "color": "black",
  "material": "canvas",
  "style": "casual",
  "shape": "rectangular"
}
"""

        response = self.model.generate_content(
            [
                prompt,
                image
            ]
        )

        text = response.text.strip()

        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        return json.loads(text)