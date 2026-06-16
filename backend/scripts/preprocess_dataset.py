import pandas as pd

TARGET_CATEGORIES = [
  "Office Electronics",
  "Headphones & Earbuds",
  "Home Storage & Organization",
  "Toys & Games",
  "Sports & Outdoor Play Toys",
  "Travel Accessories",
  "Backpacks",
  "Foot, Hand & Nail Core Products",
  "Men's Clothing",
  "Women's Clothing"
]

SAMPLES_PER_CATEGORY = 200

def main():
  print("Loading datasets...")

  products = pd.read_csv("data/raw/amazon_products.csv")

  categories = pd.read_csv("data/raw/amazon_categories.csv")

  print("Joining categories...")

  products = products.merge(
    categories,
    left_on="category_id",
    right_on="id",
    how="left"
  )
  products = products[
      products["category_name"].isin(
        TARGET_CATEGORIES
      )
  ]

  products = products[
      [
          "asin",
          "title",
          "imgUrl",
          "price",
          "stars",
          "isBestSeller",
          "boughtInLastMonth",
          "category_name"
      ]
  ]

  products = products.dropna(
      subset=[
          "title",
          "imgUrl",
          "category_name"
      ]
  )

  sampled_frames = []

  for category in TARGET_CATEGORIES:
    category_df = products[
        products["category_name"] == category
    ]

    sample_size = min(
        len(category_df),
        SAMPLES_PER_CATEGORY
    )

    sampled_frames.append(
            category_df.sample(
                n=sample_size,
                random_state=42
            )
        )

    final_df = pd.concat(
        sampled_frames,
        ignore_index=True
    )

    final_df.to_csv(
        "data/processed/products_sample.csv",
        index=False
    )

    print(f"Saved {len(final_df)} products.")
    print(
        "Output: data/processed/products_sample.csv"
    )


if __name__ == "__main__":
    main()