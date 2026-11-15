
from contextlib import asynccontextmanager
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query

from recommendation_model.svd_model import (
    SVDRecommender,
    EVENT_WEIGHTS
)
from recommendation_model.recommender import ProductRecommender
from recommendation_model.hybrid_recommender import hybrid_recommend
from recommendation_model.ncf_predict import (
    checkpoint,
    reverse_product_map
)

ROOT = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):

    # 1. Load TF-IDF model
    content = ProductRecommender()
    content.load_products()

    if content.products is None or content.products.empty:
        raise RuntimeError("Flask product API unavailable")

    if not content.build_model():
        raise RuntimeError("TF-IDF model failed")

    names = {
        int(row.id): str(row.name)
        for row in content.products.itertuples(index=False)
    }

    # 2. Verify that product IDs still match NCF
    catalogue = pd.read_csv(
        ROOT / "data" / "product_id_mapping.csv"
    )

    expected = {
        int(row.product_id): str(row.product_name)
        for row in catalogue.itertuples(index=False)
    }

    if names != expected:
        raise RuntimeError(
            "Product catalogue mismatch! "
            "NCF and Flask product IDs must match."
        )

    # 3. Load anonymous user mapping
    users = pd.read_csv(
        ROOT / "data" / "user_id_mapping.csv"
    )

    user_map = {
        int(row.ncf_user_index): int(row.anonymous_user_id)
        for row in users.itertuples(index=False)
    }

    # 4. Train SVD from the same interactions
    df = pd.read_csv(
        ROOT / "data" / "interactions_cleaned.csv"
    )

    svd = SVDRecommender(n_factors=2)

    df["strength"] = (
        df["interaction_type"]
        .map(EVENT_WEIGHTS)
        .fillna(0)
    )

    svd.ratings = (
        df.groupby(["user_id", "product_id"])["strength"]
        .sum()
        .clip(upper=5)
        .reset_index(name="rating")
    )

    svd.users = sorted(
        int(x) for x in svd.ratings["user_id"].unique()
    )

    svd.products = sorted(
        int(x) for x in svd.ratings["product_id"].unique()
    )

    svd.user_to_idx = {
        u: i for i, u in enumerate(svd.users)
    }

    svd.product_to_idx = {
        p: i for i, p in enumerate(svd.products)
    }

    svd.product_names = names
    svd.train()

    # 5. Verify user interactions match NCF
    known = checkpoint["known_interactions"]
    seen_by_user = {}

    for ncf_index, anonymous_id in user_map.items():
        indices = known.get(
            ncf_index, known.get(str(ncf_index), [])
        )

        seen = {
            int(reverse_product_map[int(i)])
            for i in indices
        }

        svd_seen = set(
            df.loc[
                df["user_id"] == anonymous_id,
                "product_id"
            ].astype(int)
        )

        if seen != svd_seen:
            raise RuntimeError(
                f"User mapping mismatch: {ncf_index}"
            )

        seen_by_user[ncf_index] = seen

    # Store models so they load only once
    app.state.content = content
    app.state.svd = svd
    app.state.names = names
    app.state.user_map = user_map
    app.state.seen = seen_by_user

    print("Hybrid recommendation API ready!")

    yield


app = FastAPI(
    title="ShopSense Recommendation API",
    version="1.0",
    lifespan=lifespan
)


@app.get("/")
def home():
    return {
        "message": "ShopSense Hybrid Recommendation API",
        "status": "running"
    }


@app.get("/recommend/{user_id}")
def get_recommendations(
    user_id: int,
    top_k: int = Query(10, ge=1, le=20)
):
    # user_id is an anonymous NCF index, NOT a live account ID
    if user_id not in app.state.user_map:
        raise HTTPException(
            status_code=404,
            detail="Unknown development user index"
        )

    svd_user_id = app.state.user_map[user_id]
    seen = app.state.seen[user_id]

    results = hybrid_recommend(
        svd_model=app.state.svd,
        content_model=app.state.content,
        svd_user_id=svd_user_id,
        ncf_user_index=user_id,
        seen_product_ids=seen,
        top_k=top_k
    )

    recommendations = []

    for item in results:
        pid = int(item["product_id"])

        recommendations.append({
            "product_id": pid,
            "name": app.state.names[pid],
            "hybrid_score": item["hybrid_score"]
        })

    return {
        "user_id": user_id,
        "model": "SVD + TF-IDF + NCF",
        "recommendations": recommendations,
        "total": len(recommendations)
    }


@app.get("/similar/{product_id}")
def get_similar_products(
    product_id: int,
    top_k: int = Query(10, ge=1, le=20)
):
    content = app.state.content

    product_ids = [
        int(x) for x in content.products["id"]
    ]

    if product_id not in product_ids:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    source_index = product_ids.index(product_id)

    scores = content.similarity_matrix[source_index]

    ranked = sorted(
        [
            (pid, float(scores[i]))
            for i, pid in enumerate(product_ids)
            if pid != product_id
        ],
        key=lambda x: x[1],
        reverse=True
    )

    recommendations = [
        {
            "product_id": pid,
            "name": app.state.names[pid],
            "similarity_score": round(score, 4)
        }
        for pid, score in ranked[:top_k]
    ]

    return {
        "product_id": product_id,
        "recommendations": recommendations,
        "total": len(recommendations)
    }
