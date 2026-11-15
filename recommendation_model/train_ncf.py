
import random
from pathlib import Path

import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from recommendation_model.ncf_model import NeuMF


# Reproducibility
random.seed(42)
torch.manual_seed(42)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MODEL_PATH = ROOT / "recommendation_model" / "ncf_model.pth"

# 1. Load the real ShopSense data
df = pd.read_csv(DATA / "interactions_cleaned.csv")
products = pd.read_csv(DATA / "product_id_mapping.csv")
users = pd.read_csv(DATA / "user_id_mapping.csv")

# 2. Convert real product IDs to embedding indices
df = df.merge(
    products[["product_id", "ncf_product_index"]],
    on="product_id",
    how="left",
    validate="many_to_one"
)

if df["ncf_product_index"].isna().any():
    raise ValueError("Some products have no NCF mapping")

user_map = dict(zip(
    users["anonymous_user_id"],
    users["ncf_user_index"]
))

df["user_index"] = df["user_id"].map(user_map)

if df["user_index"].isna().any():
    raise ValueError("Some users have no NCF mapping")

# 3. Repeated events for the same pair count as one positive
pairs = set(
    zip(
        df["user_index"].astype(int),
        df["ncf_product_index"].astype(int)
    )
)

num_users = len(users)
num_items = len(products)

all_items = set(products["ncf_product_index"].astype(int))

# All known positives, including held-out positives
known = {u: set() for u in range(num_users)}

for u, i in pairs:
    known[u].add(i)

# 4. Hold out one positive per user for validation
train_pairs = []
val_pairs = []

for u in range(num_users):
    items = sorted(known[u])
    random.shuffle(items)

    if len(items) >= 2:
        val_pairs.append((u, items[0]))
        train_pairs.extend((u, i) for i in items[1:])
    else:
        train_pairs.extend((u, i) for i in items)

print("Original interaction events:", len(df))
print("Unique positive pairs:", len(pairs))
print("Training positives:", len(train_pairs))
print("Validation positives:", len(val_pairs))


# 5. Build a PyTorch dataset
class NCFDataset(Dataset):
    def __init__(self, positive_pairs, known_pairs, negatives=4):
        self.samples = []

        for u, i in positive_pairs:
            self.samples.append((u, i, 1.0))

            # Never sample any known positive as negative
            candidates = list(all_items - known_pairs[u])

            count = min(negatives, len(candidates))
            for neg in random.sample(candidates, count):
                self.samples.append((u, neg, 0.0))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        u, i, label = self.samples[index]

        return (
            torch.tensor(u, dtype=torch.long),
            torch.tensor(i, dtype=torch.long),
            torch.tensor(label, dtype=torch.float32)
        )


dataset = NCFDataset(train_pairs, known)

loader = DataLoader(
    dataset,
    batch_size=16,
    shuffle=True
)

# 6. Initialize NeuMF
model = NeuMF(
    num_users=num_users,
    num_items=num_items,
    embedding_dim=32
)

criterion = nn.BCELoss()
optimizer = torch.optim.Adam(
    model.parameters(),
    lr=0.001
)

# 7. Train for 20 epochs
best_loss = float("inf")

for epoch in range(20):
    model.train()
    total_loss = 0.0

    for user_ids, item_ids, labels in loader:
        optimizer.zero_grad()

        predictions = model(user_ids, item_ids)
        loss = criterion(predictions, labels)

        loss.backward()
        optimizer.step()

        total_loss += loss.item() * len(labels)

    avg_loss = total_loss / len(dataset)

    print(
        f"Epoch {epoch + 1:02d}/20 | "
        f"Training Loss: {avg_loss:.4f}"
    )

    # Save the best training-loss checkpoint
    if avg_loss < best_loss:
        best_loss = avg_loss

        torch.save({
            "model_state_dict": model.state_dict(),
            "num_users": num_users,
            "num_items": num_items,
            "embedding_dim": 32,
            "user_mapping": user_map,
            "product_mapping": dict(zip(
                products["product_id"],
                products["ncf_product_index"]
            )),
            "known_interactions": {
                u: sorted(items) for u, items in known.items()
            }
        }, MODEL_PATH)

print("\nModel saved to:", MODEL_PATH)
print("Best training loss:", round(best_loss, 4))
