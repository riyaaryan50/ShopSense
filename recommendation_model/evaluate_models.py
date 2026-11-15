"""Model comparison: Popularity vs SVD vs Content-based vs NCF vs Hybrid.

Leave-one-out evaluation on data/interactions.csv (exported by
backend/scripts/seed_demo_data.py): for every user with at least two
distinct products, the most recent product is held out, every model is
trained on the remaining interactions, and the held-out product is ranked
against all products the user has not interacted with.

Metrics: Hit Rate@10, NDCG@10, MRR and training time.
Outputs (reports/): model_comparison.md, model_comparison.json,
hr_ndcg_by_model.png, ncf_training_loss.png

Run from the repository root:
    python -m recommendation_model.evaluate_models
"""

import json
import math
import random
import time
from collections import defaultdict
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from surprise import SVD, Dataset, Reader

from recommendation_model.ncf_model import NeuMF

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPORTS = ROOT / "recommendation_model" / "reports"

EVENT_WEIGHTS = {"view": 1.0, "click": 1.5, "wishlist": 2.5, "cart": 3.0, "purchase": 5.0}
HYBRID_WEIGHTS = {"svd": 0.3, "content": 0.3, "ncf": 0.4}
K = 10
SEED = 42


def set_seed(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


# ---------------------------------------------------------------------- data
def load_data():
    interactions = pd.read_csv(DATA / "interactions.csv")
    interactions["created_at"] = pd.to_datetime(interactions["created_at"], format="mixed")
    interactions["weight"] = interactions["event_type"].map(EVENT_WEIGHTS).fillna(0)
    products = pd.read_json(DATA / "products.json")
    return interactions, products


def leave_one_out(interactions):
    """Hold out each user's most recent distinct product (timestamp split).

    Returns (train ratings, {user: held-out product}, train interactions).
    """
    train_rows, test = [], {}
    for user_id, group in interactions.groupby("user_id"):
        last_seen = group.groupby("product_id")["created_at"].max().sort_values()
        if len(last_seen) < 2:
            train_rows.append(group)
            continue
        held_out = int(last_seen.index[-1])
        test[int(user_id)] = held_out
        train_rows.append(group[group["product_id"] != held_out])
    train = pd.concat(train_rows)
    ratings = (train.groupby(["user_id", "product_id"])["weight"].sum()
               .clip(upper=5).reset_index(name="rating"))
    return ratings, test, train


# ---------------------------------------------------------------------- models
def popularity_model(ratings):
    counts = ratings.groupby("product_id")["rating"].sum().to_dict()
    return lambda user, items: {i: counts.get(i, 0.0) for i in items}


def svd_model(ratings):
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(ratings[["user_id", "product_id", "rating"]], reader)
    algo = SVD(n_factors=10, n_epochs=40, random_state=SEED)
    algo.fit(data.build_full_trainset())
    return lambda user, items: {i: algo.predict(user, i).est for i in items}


def content_model(ratings, products):
    text = (products["name"] + " " + products["name"] + " " + products["category"].fillna("")
            + " " + products["description"].fillna(""))
    matrix = TfidfVectorizer(stop_words="english", ngram_range=(1, 2),
                             sublinear_tf=True).fit_transform(text)
    row = {int(pid): i for i, pid in enumerate(products["id"])}
    by_user = ratings.groupby("user_id")

    def score(user, items):
        history = by_user.get_group(user)
        weights = history["rating"].to_numpy()
        rows = [row[int(p)] for p in history["product_id"]]
        profile = np.asarray(matrix[rows].multiply(weights[:, None]).sum(axis=0)) / weights.sum()
        sims = cosine_similarity(profile, matrix).ravel()
        return {i: float(sims[row[i]]) for i in items}
    return score


def ncf_model(ratings, all_items, epochs=20, negatives=4):
    users = sorted(ratings["user_id"].unique())
    u_index = {u: i for i, u in enumerate(users)}
    i_index = {p: i for i, p in enumerate(sorted(all_items))}
    positives = defaultdict(set)
    for u, p in zip(ratings["user_id"], ratings["product_id"]):
        positives[u_index[u]].add(i_index[int(p)])

    samples = []
    item_ids = list(i_index.values())
    for u, items in positives.items():
        candidates = [i for i in item_ids if i not in items]
        for i in items:
            samples.append((u, i, 1.0))
            for n in random.sample(candidates, min(negatives, len(candidates))):
                samples.append((u, n, 0.0))
    data = torch.tensor(samples)

    model = NeuMF(len(users), len(i_index), embedding_dim=32)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = nn.BCELoss()
    losses = []
    for _ in range(epochs):
        model.train()
        perm = torch.randperm(len(data))
        total = 0.0
        for start in range(0, len(data), 64):
            batch = data[perm[start:start + 64]]
            optimizer.zero_grad()
            pred = model(batch[:, 0].long(), batch[:, 1].long())
            loss = loss_fn(pred, batch[:, 2])
            loss.backward()
            optimizer.step()
            total += loss.item() * len(batch)
        losses.append(total / len(data))
    model.eval()

    def score(user, items):
        with torch.no_grad():
            u = torch.full((len(items),), u_index[user], dtype=torch.long)
            i = torch.tensor([i_index[x] for x in items], dtype=torch.long)
            preds = model(u, i).tolist()
        return dict(zip(items, preds))
    score.losses = losses
    return score


def minmax(scores):
    low, high = min(scores.values()), max(scores.values())
    if high - low < 1e-12:
        return {k: 0.0 for k in scores}
    return {k: (v - low) / (high - low) for k, v in scores.items()}


def hybrid_model(svd, content, ncf, weights=None):
    weights = weights or HYBRID_WEIGHTS

    def score(user, items):
        parts = {"svd": minmax(svd(user, items)), "content": minmax(content(user, items)),
                 "ncf": minmax(ncf(user, items))}
        return {i: sum(weights[n] * parts[n][i] for n in parts) for i in items}
    return score


def tune_hybrid_weights(train_interactions, products, all_items):
    """Grid-search hybrid weights on a validation split carved out of the TRAIN data.

    Each user's most recent *training* product becomes the validation target, so
    the test items are never seen while tuning.
    """
    val_ratings, val_test, _ = leave_one_out(train_interactions)
    svd = svd_model(val_ratings)
    content = content_model(val_ratings, products)
    ncf = ncf_model(val_ratings, all_items)
    grid = [round(x * 0.1, 1) for x in range(11)]
    best = None
    for w_svd in grid:
        for w_cb in grid:
            w_ncf = round(1 - w_svd - w_cb, 1)
            if w_ncf < 0:
                continue
            weights = {"svd": w_svd, "content": w_cb, "ncf": w_ncf}
            metrics = evaluate(hybrid_model(svd, content, ncf, weights),
                               val_ratings, val_test, all_items)
            key = (metrics["ndcg@10"], metrics["hr@10"])
            if best is None or key > best[0]:
                best = (key, weights, metrics)
    return best[1], best[2], len(val_test)


# ---------------------------------------------------------------------- evaluation
def evaluate(scorer, ratings, test, all_items):
    seen = ratings.groupby("user_id")["product_id"].apply(lambda s: set(map(int, s))).to_dict()
    hits, ndcgs, rrs = [], [], []
    for user, held_out in test.items():
        candidates = sorted(all_items - seen.get(user, set()))
        scores = scorer(user, candidates)
        # Ties are broken pessimistically (held-out item ranked last among equals).
        target = scores[held_out]
        rank = 1 + sum(1 for i, s in scores.items() if i != held_out and s >= target)
        hits.append(1.0 if rank <= K else 0.0)
        ndcgs.append(1.0 / math.log2(rank + 1) if rank <= K else 0.0)
        rrs.append(1.0 / rank)
    return {"hr@10": float(np.mean(hits)), "ndcg@10": float(np.mean(ndcgs)),
            "mrr": float(np.mean(rrs)), "users": len(test),
            "candidates_per_user": round(float(np.mean(
                [len(all_items - seen.get(u, set())) for u in test])), 1)}


def main():
    set_seed()
    interactions, products = load_data()
    ratings, test, train_interactions = leave_one_out(interactions)
    all_items = set(int(p) for p in products["id"])

    results, models = {}, {}
    builders = [
        ("Popularity", lambda: popularity_model(ratings)),
        ("SVD (Surprise)", lambda: svd_model(ratings)),
        ("Content-based (TF-IDF)", lambda: content_model(ratings, products)),
        ("NCF (NeuMF)", lambda: ncf_model(ratings, all_items)),
    ]
    for name, build in builders:
        start = time.perf_counter()
        models[name] = build()
        train_s = time.perf_counter() - start
        results[name] = {**evaluate(models[name], ratings, test, all_items),
                         "train_seconds": round(train_s, 3)}

    hybrid = hybrid_model(models["SVD (Surprise)"], models["Content-based (TF-IDF)"],
                          models["NCF (NeuMF)"])
    results["Hybrid (0.3 SVD + 0.3 CB + 0.4 NCF)"] = {
        **evaluate(hybrid, ratings, test, all_items),
        "train_seconds": round(sum(results[n]["train_seconds"]
                                   for n in ("SVD (Surprise)", "Content-based (TF-IDF)",
                                             "NCF (NeuMF)")), 3)}

    set_seed()
    tuned, val_metrics, val_users = tune_hybrid_weights(train_interactions, products, all_items)
    tuned_label = (f"Hybrid tuned ({tuned['svd']} SVD + {tuned['content']} CB + "
                   f"{tuned['ncf']} NCF)")
    results[tuned_label] = {
        **evaluate(hybrid_model(models["SVD (Surprise)"], models["Content-based (TF-IDF)"],
                                models["NCF (NeuMF)"], tuned), ratings, test, all_items),
        "train_seconds": results["Hybrid (0.3 SVD + 0.3 CB + 0.4 NCF)"]["train_seconds"],
        "tuned_on_validation": {"weights": tuned, "validation_ndcg@10": val_metrics["ndcg@10"],
                                "validation_users": val_users}}

    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "model_comparison.json").write_text(json.dumps(results, indent=2))

    names = list(results)
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.bar(x - 0.2, [results[n]["hr@10"] for n in names], 0.4, label="HR@10", color="#7c3aed")
    ax.bar(x + 0.2, [results[n]["ndcg@10"] for n in names], 0.4, label="NDCG@10", color="#38bdf8")
    ax.set_xticks(x, [n.split(" (")[0] for n in names], fontsize=8)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Score")
    ax.set_title(f"Leave-one-out ranking quality ({results[names[0]]['users']} users)")
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(REPORTS / "hr_ndcg_by_model.png", dpi=150)

    losses = models["NCF (NeuMF)"].losses
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.plot(range(1, len(losses) + 1), losses, marker="o", color="#7c3aed")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("BCE loss")
    ax.set_title("NCF training loss")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(REPORTS / "ncf_training_loss.png", dpi=150)

    best = max(names, key=lambda n: (results[n]["ndcg@10"], results[n]["hr@10"]))
    lines = [
        "# Recommendation model comparison", "",
        "Leave-one-out evaluation on `data/interactions.csv`: each user's most recent product "
        "is held out and ranked against every product they have not interacted with. "
        "Ties count against the model.", "",
        f"Users evaluated: **{results[names[0]]['users']}** · average candidates per user: "
        f"**{results[names[0]]['candidates_per_user']}** · catalogue: {len(all_items)} products", "",
        "| Model | HR@10 | NDCG@10 | MRR | Train time (s) |", "|---|---|---|---|---|",
    ]
    for n in names:
        r = results[n]
        lines.append(f"| {n} | {r['hr@10']:.3f} | {r['ndcg@10']:.3f} | {r['mrr']:.3f} | "
                     f"{r['train_seconds']} |")
    lines += ["", f"Best NDCG@10: **{best}**.", "",
              f"Hybrid weights were tuned by grid search (step 0.1) on a separate validation "
              f"split ({val_users} users, each user's most recent *training* product), never "
              f"on the test items. Selected weights: SVD {tuned['svd']}, content "
              f"{tuned['content']}, NCF {tuned['ncf']} (validation NDCG@10 "
              f"{val_metrics['ndcg@10']:.3f}).", "",
              "![HR and NDCG by model](hr_ndcg_by_model.png)", "",
              "![NCF training loss](ncf_training_loss.png)", "",
              "Caveats: the dataset is small (20 products, demo users and reviewers with "
              "synthetic histories), so differences between models are noisy. Re-run this "
              "script on real interaction data before drawing conclusions."]
    (REPORTS / "model_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
