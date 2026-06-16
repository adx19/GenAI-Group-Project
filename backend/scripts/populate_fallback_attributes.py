import app.models

from app.database.session import SessionLocal

from app.models.product import Product
from app.models.product_attribute import ProductAttribute


CATEGORY_DEFAULTS = {
    "Office Electronics": {
        "color": "black",
        "material": "plastic",
        "style": "professional",
        "shape": "rectangular",
    },
    "Headphones & Earbuds": {
        "color": "black",
        "material": "plastic",
        "style": "modern",
        "shape": "rounded",
    },
    "Home Storage & Organization": {
        "color": "white",
        "material": "plastic",
        "style": "functional",
        "shape": "rectangular",
    },
    "Backpacks": {
        "color": "black",
        "material": "fabric",
        "style": "casual",
        "shape": "rectangular",
    },
    "Men's Clothing": {
        "color": "black",
        "material": "cotton",
        "style": "casual",
        "shape": "t-shirt",
    },
    "Women's Clothing": {
        "color": "pink",
        "material": "cotton",
        "style": "casual",
        "shape": "dress",
    },
    "Toys & Games": {
        "color": "multi-color",
        "material": "plastic",
        "style": "playful",
        "shape": "irregular",
    },
    "Sports & Outdoor Play Toys": {
        "color": "multi-color",
        "material": "plastic",
        "style": "active",
        "shape": "round",
    },
    "Travel Accessories": {
        "color": "black",
        "material": "fabric",
        "style": "travel",
        "shape": "rectangular",
    },
}


def main():

    db = SessionLocal()

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

        inserted = 0

        for product in products:

            defaults = CATEGORY_DEFAULTS.get(
                product.category,
                {
                    "color": "black",
                    "material": "plastic",
                    "style": "standard",
                    "shape": "rectangular",
                }
            )

            attribute = ProductAttribute(
                product_id=product.id,
                color=defaults["color"],
                material=defaults["material"],
                style=defaults["style"],
                shape=defaults["shape"]
            )

            db.add(attribute)

            inserted += 1

            if inserted % 100 == 0:

                print(
                    f"Inserted {inserted} attributes..."
                )

        db.commit()

        print(
            f"\nSuccessfully inserted "
            f"{inserted} fallback attributes"
        )

    except Exception as e:

        db.rollback()

        print(
            "Failed to populate fallback attributes"
        )

        print(e)

    finally:

        db.close()


if __name__ == "__main__":
    main()