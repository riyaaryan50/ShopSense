
import random
from pathlib import Path

import pandas as pd
import torch

from recommendation_model.ncf_model import NeuMF

ROOT = Path(__file__).resolve().parent.parent

# Load the saved checkpoint.
# Only load checkpoint files you trust.
checkpoint = torch.load(
    ROOT / "recommendation_model" / "ncf_model.pth",
    map_location="cpu",
    weights_only=False
)

model = NeuMF(
    num_users=checkpoint["num_users"],
    num_items=checkpoint["num_items"],
    embedding_dim=checkpoint["embedding_dim"]
)

model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

# Reconstruct the same validation split used in training
random.seed(42)

df = pd.read_csv(ROOT / "data" / "interactions_cleaned.csv")
products = pd.read_csv(ROOT / "data" / "product_id_mapping.csv")
users = pd.read_csv(ROOT / "data" / "user_id_mapping.csv")

df = df.merge(
    products[["product_id", "ncf_product_index"]],
    on="product_id",
    validate="many_to_one"
)

user_map = dict(zip(
    users["anonymous_user_id"],
    users["ncf_user_index"]
))

df["user_index"] = df["user_id"].map(user_map)

pairs = set(zip(
    df["user_index"].astype(int),
    df["ncf_product_index"].astype(int)
))

known = {u: set() for u in range(checkpoint["num_users"])}

for u, i in pairs:
    known[u].add(i)

validation = []

for u in range(checkpoint["num_users"]):
    items = sorted(known[u])
    random.shuffle(items)

    if len(items) >= 2:
        validation.append((u, items[0]))

all_items = set(products["ncf_product_index"].astype(int))


def rank_products(user_id, held_out_item):
    # Exclude training positives, but retain the held-out item
    excluded = known[user_id] - {held_out_item}
    candidates = sorted(all_items - excluded)

    user_tensor = torch.tensor(
        [user_id] * len(candidates), dtype=torch.long
    )
    item_tensor = torch.tensor(
        candidates, dtype=torch.long
    )

    with torch.no_grad():
        scores = model(user_tensor, item_tensor).tolist()

    ranked = sorted(
        zip(candidates, scores),
        key=lambda x: x[1],
        reverse=True
    )

    return [item for item, score in ranked]


hits = []
ndcgs = []
reciprocal_ranks = []

for user_id, held_out_item in validation:
    ranked = rank_products(user_id, held_out_item)

    rank = ranked.index(held_out_item) + 1

    hit = 1.0 if rank <= 10 else 0.0
    ndcg = 1.0 / __import__("math").log2(rank + 1) if rank <= 10 else 0.0
    rr = 1.0 / rank

    hits.append(hit)
    ndcgs.append(ndcg)
    reciprocal_ranks.append(rr)

    print(f"User {user_id}: held-out product rank = {rank}")

if validation:
    print(f"\nHit Rate@10: {sum(hits) / len(hits):.4f}")
    print(f"NDCG@10: {sum(ndcgs) / len(ndcgs):.4f}")
    print(f"MRR: {sum(reciprocal_ranks) / len(reciprocal_ranks):.4f}")
else:
    print("Not enough validation data.")

