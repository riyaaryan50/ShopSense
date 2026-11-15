
from recommendation_model.recommender import ProductRecommender
from recommendation_model.hybrid_recommender import hybrid_recommend
from recommendation_model.ncf_predict import (
    checkpoint,
    reverse_product_map
)

# Anonymous NCF user index
USER_INDEX = 1

# Step 1: Load TF-IDF model
content_model = ProductRecommender()
content_model.load_products()

if content_model.products is None or content_model.products.empty:
    raise RuntimeError("No products loaded from Flask API")

if not content_model.build_model():
    raise RuntimeError("TF-IDF model failed")

# Step 2: Find products already viewed or interacted with
known = checkpoint["known_interactions"]

seen_indices = known.get(
    USER_INDEX,
    known.get(str(USER_INDEX), [])
)

seen_product_ids = [
    int(reverse_product_map[int(i)])
    for i in seen_indices
]

print("\nNCF User:", USER_INDEX)
print("Already interacted products:", seen_product_ids)

# Step 3: Combine NCF + TF-IDF
# SVD will be added after verifying its user mapping.
results = hybrid_recommend(
    svd_model=None,
    content_model=content_model,
    svd_user_id=None,
    ncf_user_index=USER_INDEX,
    seen_product_ids=seen_product_ids,
    top_k=10
)

# Step 4: Display real product names
names = dict(zip(
    content_model.products["id"].astype(int),
    content_model.products["name"]
))

print("\n===== HYBRID RECOMMENDATIONS =====\n")

for rank, item in enumerate(results, start=1):
    pid = int(item["product_id"])

    print(
        f"{rank}. {names[pid]} | "
        f"Product ID: {pid} | "
        f"Hybrid Score: {item['hybrid_score']}"
    )

print("\nTotal recommendations:", len(results))

