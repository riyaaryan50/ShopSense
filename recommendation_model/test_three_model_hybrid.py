
from pathlib import Path

import pandas as pd

from recommendation_model.recommender import ProductRecommender
from recommendation_model.svd_model import (
    SVDRecommender,
    EVENT_WEIGHTS
)
from recommendation_model.ncf_predict import (
    checkpoint,
    reverse_product_map
)
from recommendation_model.hybrid_recommender import (
    hybrid_recommend
)

ROOT = Path(__file__).resolve().parent.parent
USER_INDEX = 1

# --------------------------------
# 1. Load and build TF-IDF
# --------------------------------
content_model = ProductRecommender()
content_model.load_products()

if content_model.products is None or content_model.products.empty:
    raise RuntimeError("Flask product API returned no products")

if not content_model.build_model():
    raise RuntimeError("TF-IDF model failed")

names = {
    int(row.id): row.name
    for row in content_model.products.itertuples(index=False)
}

# --------------------------------
# 2. Load the SAME dataset as NCF
# --------------------------------
df = pd.read_csv(
    ROOT / "data" / "interactions_cleaned.csv"
)

user_mapping = pd.read_csv(
    ROOT / "data" / "user_id_mapping.csv"
)

# Map NCF index to its anonymous source user ID.
# Never assume these IDs are interchangeable.
matching = user_mapping.loc[
    user_mapping["ncf_user_index"] == USER_INDEX,
    "anonymous_user_id"
]

if len(matching) != 1:
    raise RuntimeError("NCF user mapping not found")

svd_user_id = int(matching.iloc[0])

# Verify every interaction belongs to our product catalogue
dataset_ids = set(df["product_id"].astype(int))

if not dataset_ids.issubset(set(names)):
    raise RuntimeError("SVD dataset has unknown product IDs")

# --------------------------------
# 3. Build SVD using the same data
# --------------------------------
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
    user: idx for idx, user in enumerate(svd.users)
}

svd.product_to_idx = {
    pid: idx for idx, pid in enumerate(svd.products)
}

svd.product_names = names

svd.train()

# --------------------------------
# 4. Get NCF user's known products
# --------------------------------
known = checkpoint["known_interactions"]

seen_indices = known.get(
    USER_INDEX,
    known.get(str(USER_INDEX), [])
)

seen_product_ids = {
    int(reverse_product_map[int(i)])
    for i in seen_indices
}

# Verify NCF and SVD represent the SAME user
svd_seen_ids = set(
    df.loc[
        df["user_id"] == svd_user_id,
        "product_id"
    ].astype(int)
)

if seen_product_ids != svd_seen_ids:
    raise RuntimeError(
        "NCF and SVD user interactions do not match"
    )

print("\nNCF user index:", USER_INDEX)
print("SVD anonymous user ID:", svd_user_id)
print("Already interacted:", sorted(seen_product_ids))

# --------------------------------
# 5. Combine SVD + TF-IDF + NCF
# --------------------------------
results = hybrid_recommend(
    svd_model=svd,
    content_model=content_model,
    svd_user_id=svd_user_id,
    ncf_user_index=USER_INDEX,
    seen_product_ids=seen_product_ids,
    top_k=10
)

# --------------------------------
# 6. Display recommendations
# --------------------------------
print("\n===== THREE-MODEL HYBRID =====\n")

for rank, item in enumerate(results, start=1):
    pid = int(item["product_id"])

    print(
        f"{rank}. {names[pid]} | "
        f"Product ID: {pid} | "
        f"Hybrid Score: {item['hybrid_score']}"
    )

print("\nTotal recommendations:", len(results))
