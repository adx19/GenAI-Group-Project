import os
import time
import app.models

from app.database.session import SessionLocal

from app.models.product import Product
from app.models.product_attribute import ProductAttribute

from app.services.ai.attribute_extractor import AttributeExtractor


REQUEST_DELAY = 15
RATE_LIMIT_DELAY = 30
MAX_RETRIES = 10


def main():

    db = SessionLocal()

    extractor = AttributeExtractor()

    try:

        products = (
            db.query(Product)
            .outerjoin(
                ProductAttribute,
                Product.id == ProductAttribute.product_id
            )
            .filter(
                ProductAttribute.id == None
            )
            .all()
        )

        print(
            f"Found {len(products)} products without attributes"
        )

        for product in products:

            image_path = (
                f"data/images/{product.id}.jpg"
            )

            if not os.path.exists(image_path):

                print(
                    f"Missing image: {product.id}"
                )

                continue

            retries = 0

            while retries < MAX_RETRIES:

                try:

                    print(f"Starting Gemini call for {product.id}")

                    attributes = (
                        extractor.extract_attributes(
                            image_path
                        )
                    )

                    attribute = ProductAttribute(
                        product_id=product.id,
                        color=attributes.get("color"),
                        material=attributes.get("material"),
                        style=attributes.get("style"),
                        shape=attributes.get("shape")
                    )

                    db.add(attribute)

                    db.commit()

                    print(
                        f"Processed {product.id}"
                    )

                    time.sleep(
                        REQUEST_DELAY
                    )

                    break

                except Exception as e:

                    db.rollback()

                    error_text = str(e)

                    if "429" in error_text:

                        retries += 1

                        print(
                            f"Rate limited on product "
                            f"{product.id}"
                        )

                        print(
                            f"Retry {retries}/"
                            f"{MAX_RETRIES}"
                        )

                        print(
                            f"Waiting "
                            f"{RATE_LIMIT_DELAY}s..."
                        )

                        time.sleep(
                            RATE_LIMIT_DELAY
                        )

                    else:

                        print(
                            f"Failed {product.id}"
                        )

                        print(e)

                        break

            else:

                print(
                    f"Skipped {product.id} "
                    f"after {MAX_RETRIES} retries"
                )

    finally:

        db.close()


if __name__ == "__main__":
    main()