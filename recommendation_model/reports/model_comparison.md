# Recommendation model comparison

Leave-one-out evaluation on `data/interactions.csv`: each user's most recent product is held out and ranked against every product they have not interacted with. Ties count against the model.

Users evaluated: **19** · average candidates per user: **7.7** · catalogue: 20 products

| Model | HR@10 | NDCG@10 | MRR | Train time (s) |
|---|---|---|---|---|
| Popularity | 0.947 | 0.373 | 0.204 | 0.009 |
| SVD (Surprise) | 0.947 | 0.412 | 0.250 | 0.03 |
| Content-based (TF-IDF) | 0.947 | 0.576 | 0.465 | 0.177 |
| NCF (NeuMF) | 1.000 | 0.569 | 0.434 | 33.947 |
| Hybrid (0.3 SVD + 0.3 CB + 0.4 NCF) | 0.895 | 0.559 | 0.460 | 34.154 |
| Hybrid tuned (0.1 SVD + 0.5 CB + 0.4 NCF) | 0.895 | 0.557 | 0.458 | 34.154 |

Best NDCG@10: **Content-based (TF-IDF)**.

Hybrid weights were tuned by grid search (step 0.1) on a separate validation split (19 users, each user's most recent *training* product), never on the test items. Selected weights: SVD 0.1, content 0.5, NCF 0.4 (validation NDCG@10 0.574).

![HR and NDCG by model](hr_ndcg_by_model.png)

![NCF training loss](ncf_training_loss.png)

Caveats: the dataset is small (20 products, demo users and reviewers with synthetic histories), so differences between models are noisy. Re-run this script on real interaction data before drawing conclusions.
