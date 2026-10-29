from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

DATA_FILE = Path(__file__).resolve().parent / "data" / "amazon.csv"


def load_products():
    """Step 1: load the CSV and clean it."""
    df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
    df.columns = df.columns.str.strip().str.lower()

    # Give the columns simpler names
    df = df.rename(columns={
        "discounted_price": "price",
        "discount_percentage": "discount",
        "about_product": "description",
        "img_link": "image_link",
    })

    df = df[["product_id", "product_name", "category", "price", "actual_price",
             "discount", "rating", "description", "image_link", "product_link"]].copy()

    # "₹1,299" or "42%" -> 1299 or 42  (keep only digits and the dot)
    for col in ["price", "actual_price", "discount", "rating"]:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(r"[^\d.]", "", regex=True),
            errors="coerce",
        )

    # Fill small gaps, drop rows missing the important stuff
    for col in ["actual_price", "discount", "rating"]:
        df[col] = df[col].fillna(df[col].median())
    df = df.fillna({"image_link": "", "product_link": ""})
    df = df.dropna(subset=["product_id", "product_name", "category",
                           "description", "price"])

    df = df.drop_duplicates(subset="product_id").reset_index(drop=True)
    return df


def build_model(products):
    """Step 2: turn text into numbers (TF-IDF) and fit the KNN model."""
    text = (products["product_name"] + " "
            + products["category"].str.replace("|", " ", regex=False) + " "
            + products["description"])

    features = TfidfVectorizer(stop_words="english", max_features=5000).fit_transform(text)

    model = NearestNeighbors(metric="cosine")
    model.fit(features)
    return model, features


def recommend_products(product_index, products, model, features, n=5):
    """Step 3: find the n most similar products."""
    n = max(1, min(n, len(products) - 1))

    # n + 1 because the closest product is always the product itself
    distances, indices = model.kneighbors(features[product_index], n_neighbors=n + 1)

    result = products.iloc[indices[0][1:]].copy()
    result["similarity"] = ((1 - distances[0][1:]) * 100).round(1).clip(0, 100)
    return result