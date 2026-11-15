
import torch
from pathlib import Path

from recommendation_model.ncf_model import NeuMF

ROOT = Path(__file__).resolve().parent

checkpoint = torch.load(
    ROOT / "ncf_model.pth",
    map_location="cpu",
    weights_only=False
)

model = NeuMF(
    checkpoint["num_users"],
    checkpoint["num_items"],
    checkpoint["embedding_dim"]
)

model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

# Convert real product IDs to NCF indices
product_map = {
    int(pid): int(idx)
    for pid, idx in checkpoint["product_mapping"].items()
}

reverse_product_map = {
    idx: pid for pid, idx in product_map.items()
}


def recommend(user_id, top_k=10):
    user_id = int(user_id)

    if not 0 <= user_id < checkpoint["num_users"]:
        raise ValueError(
            "Unknown NCF user index; use a popularity fallback"
        )

    # Exclude products the user already interacted with
    known = checkpoint["known_interactions"]
    interacted = set(
        known.get(user_id, known.get(str(user_id), []))
    )

    candidates = [
        i for i in sorted(reverse_product_map)
        if i not in interacted
    ]

    if not candidates:
        return []

    users = torch.tensor(
        [user_id] * len(candidates),
        dtype=torch.long
    )

    items = torch.tensor(candidates, dtype=torch.long)

    with torch.no_grad():
        scores = model(users, items).tolist()

    ranked = sorted(
        zip(candidates, scores),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        {
            "product_id": reverse_product_map[item],
            "ncf_score": round(score, 4)
        }
        for item, score in ranked[:top_k]
    ]


if __name__ == "__main__":
    for result in recommend(user_id=1, top_k=10):
        print(result)
