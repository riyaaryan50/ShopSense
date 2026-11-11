
import os
import pickle
import requests
import numpy as np
import pandas as pd

from sklearn.metrics import mean_squared_error, mean_absolute_error


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(BASE_DIR, "interactions.csv")
MODEL_FILE = os.path.join(BASE_DIR, "svd_model.pkl")

PRODUCT_API = "http://127.0.0.1:5000/api/products/"

EVENT_WEIGHTS = {
    "view": 1.0,
    "click": 1.5,
    "wishlist": 2.5,
    "cart": 3.0,
    "purchase": 5.0
}


class SVDRecommender:

    def __init__(self, n_factors=2):

        self.n_factors = n_factors

        self.ratings = None
        self.users = None
        self.products = None

        self.user_to_idx = {}
        self.product_to_idx = {}

        self.full_matrix = None
        self.predicted_matrix = None

        self.product_names = {}

    # --------------------------------
    # LOAD INTERACTION DATA
    # --------------------------------

    def load_data(self):

        df = pd.read_csv(DATA_FILE)

        df["user_id"] = df["user_id"].astype(int)
        df["product_id"] = df["product_id"].astype(int)

        df["strength"] = (
            df["event_type"]
            .map(EVENT_WEIGHTS)
            .fillna(0)
        )

        # Combine repeated interactions
        self.ratings = (
            df.groupby(["user_id", "product_id"])["strength"]
            .sum()
            .clip(upper=5)
            .reset_index(name="rating")
        )

        self.users = sorted(self.ratings["user_id"].unique())
        self.products = sorted(self.ratings["product_id"].unique())

        self.user_to_idx = {
            user: index
            for index, user in enumerate(self.users)
        }

        self.product_to_idx = {
            product: index
            for index, product in enumerate(self.products)
        }

        print("Interaction data loaded successfully.")
        print("Users:", len(self.users))
        print("Products:", len(self.products))
        print("User-product ratings:", len(self.ratings))

    # --------------------------------
    # CREATE USER-ITEM MATRIX
    # --------------------------------

    def create_matrix(self, data):

        matrix = np.zeros(
            (len(self.users), len(self.products))
        )

        for _, row in data.iterrows():

            u = self.user_to_idx[row["user_id"]]
            p = self.product_to_idx[row["product_id"]]

            matrix[u, p] = row["rating"]

        return matrix

    # --------------------------------
    # APPLY SVD
    # --------------------------------

    def apply_svd(self, matrix):

        U, sigma, Vt = np.linalg.svd(
            matrix,
            full_matrices=False
        )

        k = min(self.n_factors, len(sigma))

        reconstructed = (
            U[:, :k] * sigma[:k]
        ) @ Vt[:k, :]

        return reconstructed

    # --------------------------------
    # EVALUATE MODEL
    # --------------------------------

    def evaluate(self):

        rng = np.random.default_rng(42)

        test_indices = []

        # Keep at least one training item per user
        for _, group in self.ratings.groupby("user_id"):

            if len(group) < 2:
                continue

            test_count = max(
                1,
                round(len(group) * 0.2)
            )

            test_count = min(
                test_count,
                len(group) - 1
            )

            selected = rng.choice(
                group.index.to_numpy(),
                size=test_count,
                replace=False
            )

            test_indices.extend(selected.tolist())

        test_data = self.ratings.loc[test_indices]

        train_data = self.ratings.drop(
            index=test_indices
        )

        train_matrix = self.create_matrix(train_data)

        predictions = self.apply_svd(train_matrix)

        actual = []
        predicted = []

        for _, row in test_data.iterrows():

            u = self.user_to_idx[row["user_id"]]
            p = self.product_to_idx[row["product_id"]]

            actual.append(row["rating"])
            predicted.append(predictions[u, p])

        if not actual:

            print("Not enough data for evaluation.")
            return

        rmse = np.sqrt(
            mean_squared_error(actual, predicted)
        )

        mae = mean_absolute_error(
            actual,
            predicted
        )

        # Hit Rate@10
        hits = 0
        evaluated_users = 0

        for user_id, group in test_data.groupby("user_id"):

            u = self.user_to_idx[user_id]

            seen = set(
                train_data.loc[
                    train_data["user_id"] == user_id,
                    "product_id"
                ]
            )

            candidates = [
                p for p in self.products
                if p not in seen
            ]

            ranked = sorted(
                candidates,
                key=lambda p: predictions[
                    u, self.product_to_idx[p]
                ],
                reverse=True
            )

            top_10 = ranked[:10]

            actual_items = set(group["product_id"])

            if actual_items.intersection(top_10):
                hits += 1

            evaluated_users += 1

        hit_rate = (
            hits / evaluated_users
            if evaluated_users else 0
        )

        print("\n===== SVD MODEL EVALUATION =====")

        print(f"RMSE       : {rmse:.4f}")
        print(f"MAE        : {mae:.4f}")
        print(f"Hit Rate@10: {hit_rate:.4f}")

        print("Evaluated users:", evaluated_users)

    # --------------------------------
    # TRAIN FINAL MODEL
    # --------------------------------

    def train(self):

        self.full_matrix = self.create_matrix(
            self.ratings
        )

        self.predicted_matrix = self.apply_svd(
            self.full_matrix
        )

        print("\nSVD model trained successfully.")

    # --------------------------------
    # LOAD PRODUCT NAMES
    # --------------------------------

    def load_product_names(self):

        try:

            response = requests.get(
                PRODUCT_API,
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            if isinstance(data, dict):
                data = data.get("products", [])

            self.product_names = {
                int(p["id"]): p["name"]
                for p in data
            }

        except Exception as error:

            print("Product names unavailable:", error)

    # --------------------------------
    # GENERATE RECOMMENDATIONS
    # --------------------------------

    def recommend(self, user_id, top_n=10):

        user_id = int(user_id)

        # Cold-start: unknown user
        if user_id not in self.user_to_idx:

            popularity = self.full_matrix.sum(axis=0)

            ranked_indices = np.argsort(
                popularity
            )[::-1]

            return [
                {
                    "product_id": self.products[i],
                    "name": self.product_names.get(
                        self.products[i],
                        f"Product {self.products[i]}"
                    ),
                    "score": round(float(popularity[i]), 4)
                }
                for i in ranked_indices[:top_n]
                if popularity[i] > 0
            ]

        u = self.user_to_idx[user_id]

        seen = set(
            self.ratings.loc[
                self.ratings["user_id"] == user_id,
                "product_id"
            ]
        )

        ranked_indices = np.argsort(
            self.predicted_matrix[u]
        )[::-1]

        recommendations = []

        for index in ranked_indices:

            product_id = self.products[index]

            if product_id in seen:
                continue

            recommendations.append({
                "product_id": product_id,
                "name": self.product_names.get(
                    product_id,
                    f"Product {product_id}"
                ),
                "score": round(
                    float(self.predicted_matrix[u, index]),
                    4
                )
            })

            if len(recommendations) >= top_n:
                break

        return recommendations


    # --------------------------------
    # SAVE MODEL
    # --------------------------------

    def save_model(self):

        model_data = {
            "users": self.users,
            "products": self.products,
            "user_to_idx": self.user_to_idx,
            "product_to_idx": self.product_to_idx,
            "full_matrix": self.full_matrix,
            "predicted_matrix": self.predicted_matrix,
            "ratings": self.ratings,
            "product_names": self.product_names
        }

        with open(MODEL_FILE, "wb") as file:
            pickle.dump(model_data, file)

        print("\nSVD model data saved successfully.")




# --------------------------------
# MAIN EXECUTION
# --------------------------------

if __name__ == "__main__":

    model = SVDRecommender(n_factors=2)

    # Load interaction data
    model.load_data()

    # Evaluate SVD model
    model.evaluate()

    # Train final model
    model.train()

    # Load product names
    model.load_product_names()

    # Save trained model
    model.save_model()

    # Test recommendations for User 1
    test_user_id = 1

    print(
        f"\n===== TOP 10 RECOMMENDATIONS FOR USER {test_user_id} ====="
    )

    results = model.recommend(
        user_id=test_user_id,
        top_n=10
    )

    if results:
        for item in results:
            print(
                item["product_id"],
                item["name"],
                item["score"]
            )
    else:
        print("No recommendations available.")
