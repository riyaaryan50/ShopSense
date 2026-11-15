"""Collaborative filtering with the Surprise library's SVD (sprint plan, Member 2).

Implicit feedback is turned into 1-5 ratings (view=1 ... purchase=5, summed and
capped), the model is trained with Surprise SVD, evaluated on a timestamp split
(80/20 per user) with RMSE, MAE and Hit Rate@10, and saved to surprise_svd.pkl.

Train:   python -m recommendation_model.surprise_svd      (from the repo root)
Serve:   recommendation_api.py exposes /collab/recommend/<user_id> and
         /collab/predict/<user_id>/<product_id>
"""

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from surprise import SVD, Dataset, Reader, accuracy

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "interactions.csv"
MODEL_FILE = Path(__file__).resolve().parent / "surprise_svd.pkl"
EVENT_WEIGHTS = {"view": 1.0, "click": 1.5, "wishlist": 2.5, "cart": 3.0, "purchase": 5.0}


def load_ratings(path=DATA_FILE):
    df = pd.read_csv(path)
    df["created_at"] = pd.to_datetime(df["created_at"], format="mixed")
    df["weight"] = df["event_type"].map(EVENT_WEIGHTS).fillna(0)
    ratings = (df.groupby(["user_id", "product_id"])
               .agg(rating=("weight", "sum"), last=("created_at", "max"))
               .reset_index())
    ratings["rating"] = ratings["rating"].clip(1, 5)
    return ratings


def split_by_time(ratings, test_share=0.2):
    train, test = [], []
    for _, group in ratings.sort_values("last").groupby("user_id"):
        n_test = int(round(len(group) * test_share)) if len(group) >= 3 else 0
        train.append(group.iloc[:len(group) - n_test])
        if n_test:
            test.append(group.iloc[len(group) - n_test:])
    return pd.concat(train), (pd.concat(test) if test else ratings.iloc[0:0])


def fit(ratings, n_factors=10, n_epochs=40, seed=42):
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(ratings[["user_id", "product_id", "rating"]], reader)
    algo = SVD(n_factors=n_factors, n_epochs=n_epochs, random_state=seed)
    algo.fit(data.build_full_trainset())
    return algo


class SurpriseRecommender:
    def __init__(self, algo, ratings):
        self.algo = algo
        self.seen = ratings.groupby("user_id")["product_id"].apply(set).to_dict()
        self.products = sorted(ratings["product_id"].unique())
        self.popularity = ratings.groupby("product_id")["rating"].sum().to_dict()

    def predict(self, user_id, product_id):
        return float(self.algo.predict(int(user_id), int(product_id)).est)

    def recommend(self, user_id, top_n=10):
        user_id = int(user_id)
        if user_id not in self.seen:  # cold start -> popularity baseline
            ranked = sorted(self.products, key=lambda p: self.popularity.get(p, 0), reverse=True)
            return "popularity", [{"product_id": int(p), "score": round(self.popularity[p], 3)}
                                  for p in ranked[:top_n]]
        candidates = [p for p in self.products if p not in self.seen[user_id]]
        scored = sorted(((self.predict(user_id, p), p) for p in candidates), reverse=True)
        return "svd", [{"product_id": int(p), "score": round(s, 4)} for s, p in scored[:top_n]]


def evaluate(ratings):
    train, test = split_by_time(ratings)
    algo = fit(train)
    reader = Reader(rating_scale=(1, 5))
    testset = list(zip(test["user_id"], test["product_id"], test["rating"]))
    predictions = algo.test(testset)
    rmse = accuracy.rmse(predictions, verbose=False)
    mae = accuracy.mae(predictions, verbose=False)

    rec = SurpriseRecommender(algo, train)
    hits = []
    for user_id, group in test.groupby("user_id"):
        _, top = rec.recommend(user_id, top_n=10)
        hits.append(bool(set(group["product_id"]) & {t["product_id"] for t in top}))
    del reader
    return {"rmse": round(float(rmse), 4), "mae": round(float(mae), 4),
            "hit_rate@10": round(float(np.mean(hits)), 4) if hits else None,
            "test_pairs": len(test), "users": len(hits)}


def train_and_save():
    ratings = load_ratings()
    metrics = evaluate(ratings)
    # Store plain objects (not our class) so the pickle loads however the API is started.
    with open(MODEL_FILE, "wb") as handle:
        pickle.dump({"algo": fit(ratings), "ratings": ratings, "metrics": metrics}, handle)
    return metrics


def load():
    with open(MODEL_FILE, "rb") as handle:
        saved = pickle.load(handle)
    return SurpriseRecommender(saved["algo"], saved["ratings"])


if __name__ == "__main__":
    print("Surprise SVD evaluation:", train_and_save())
    print("Saved", MODEL_FILE)
