
import requests
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


API_URL = "http://127.0.0.1:5000/api/products/"


class ProductRecommender:

    def __init__(self):
        self.products = None
        self.similarity_matrix = None

    def load_products(self):
        """Fetch products from the ShopSense Flask backend."""

        try:
            response = requests.get(API_URL, timeout=10)
            response.raise_for_status()

            data = response.json()

            if isinstance(data, dict):
                data = data.get("products", [])

            if not data:
                raise ValueError("No products found in the backend.")

            self.products = pd.DataFrame(data)

            for column in ["id", "name", "description", "category"]:
                if column not in self.products.columns:
                    self.products[column] = ""

            self.products = self.products.fillna("")

            print(f"Successfully loaded {len(self.products)} products.")
            return True

        except Exception as error:
            print("Error loading products:", error)
            return False

    def build_model(self):
        """Build TF-IDF features and calculate cosine similarity."""

        if self.products is None or self.products.empty:
            print("Please load products first.")
            return False

        self.products["features"] = (
            self.products["name"].astype(str) + " " +
            self.products["description"].astype(str) + " " +
            self.products["category"].astype(str)
        )

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2)
        )

        tfidf_matrix = vectorizer.fit_transform(
            self.products["features"]
        )

        self.similarity_matrix = cosine_similarity(tfidf_matrix)

        print("TF-IDF model built successfully.")
        print("Cosine similarity matrix created.")

        return True

    def recommend(self, product_id, top_n=5):
        """Recommend similar products for a given product ID."""

        if self.products is None or self.similarity_matrix is None:
            print("Please load products and build the model first.")
            return []

        matching_indices = self.products.index[
            self.products["id"].astype(str) == str(product_id)
        ].tolist()

        if not matching_indices:
            print(f"Product ID {product_id} not found.")
            return []

        product_index = matching_indices[0]

        scores = list(enumerate(
            self.similarity_matrix[product_index]
        ))

        scores.sort(
            key=lambda item: item[1],
            reverse=True
        )

        scores = [
            item for item in scores
            if item[0] != product_index
        ]

        recommended_indices = [
            index for index, score in scores[:top_n]
        ]

        recommendations = self.products.iloc[
            recommended_indices
        ].copy()

        return recommendations.drop(
            columns=["features"],
            errors="ignore"
        ).to_dict(orient="records")


if __name__ == "__main__":

    recommender = ProductRecommender()

    if recommender.load_products():

        if recommender.build_model():

            # Test recommendations for product ID 7
            results = recommender.recommend(
                product_id=7,
                top_n=5
            )

            print("\nRecommended Products:\n")

            for product in results:
                print(
                    product["name"],
                    "-",
                    product.get("category", "")
                )
