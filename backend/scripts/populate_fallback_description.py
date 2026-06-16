import app.models

from app.database.session import SessionLocal
from app.models.product import Product


CATEGORY_DESCRIPTIONS = {
    "Office Electronics":
        "Professional office electronics designed to improve productivity, communication, and workplace efficiency.",

    "Travel Accessories":
        "Practical travel accessories created to make journeys more comfortable, organized, and convenient.",

    "Headphones & Earbuds":
        "Audio products designed to deliver immersive sound quality, comfort, and everyday listening convenience.",

    "Home Storage & Organization":
        "Functional storage and organization solutions that help maximize space and maintain a tidy home.",

    "Backpacks":
        "Durable and versatile backpacks suitable for work, school, travel, and everyday use.",

    "Men's Clothing":
        "Comfortable and stylish men's apparel designed for everyday wear and modern lifestyles.",

    "Women's Clothing":
        "Fashionable women's clothing that combines comfort, versatility, and contemporary style.",

    "Toys & Games":
        "Fun and engaging toys and games designed to entertain, educate, and encourage creativity.",

    "Sports & Outdoor Play Toys":
        "Active play products that encourage outdoor recreation, exercise, and family fun."
}


def main():

    db = SessionLocal()

    try:

        products = (
            db.query(Product)
            .filter(
                (Product.description == None) |
                (Product.description == "")
            )
            .all()
        )

        print(
            f"Found {len(products)} products without descriptions"
        )

        updated = 0

        for product in products:

            product.description = CATEGORY_DESCRIPTIONS.get(
                product.category,
                "A quality product available in our catalog."
            )

            updated += 1

        db.commit()

        print(
            f"Updated {updated} products"
        )

    except Exception as e:

        db.rollback()

        print(e)

    finally:

        db.close()


if __name__ == "__main__":
    main()