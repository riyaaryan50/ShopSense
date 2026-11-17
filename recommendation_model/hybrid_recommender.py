
from recommendation_model.ncf_predict import recommend as ncf_recommend


def normalize(scores):
    """Min-max normalize product scores to 0-1."""
    if not scores:
        return {}

    values = list(scores.values())
    low, high = min(values), max(values)

    if high == low:
        return {
            pid: (1.0 if high > 0 else 0.0)
            for pid in scores
        }

    return {
        pid: (score - low) / (high - low)
        for pid, score in scores.items()
    }


def hybrid_recommend(
    svd_model,
    content_model,
    svd_user_id=None,
    ncf_user_index=None,
    seen_product_ids=None,
    top_k=10
):
    """
    Combine SVD, TF-IDF and NCF recommendation scores.

    svd_user_id: original user ID known to the SVD model
    ncf_user_index: anonymous NCF index (0, 1, 2)
    seen_product_ids: real product IDs interacted with by this user
    """

    seen = set(int(x) for x in (seen_product_ids or []))

    # Real product IDs from the TF-IDF catalogue
    product_ids = [
        int(x) for x in content_model.products["id"].tolist()
    ]

    candidates = [
        pid for pid in product_ids if pid not in seen
    ]

    if not candidates:
        return []

    # 1. SVD scores
    svd_scores = {}

    if svd_user_id is not None:
        svd_results = svd_model.recommend(
            svd_user_id,
            top_n=len(product_ids)
        )

        svd_scores = {
            int(item["product_id"]): float(item["score"])
            for item in svd_results
            if int(item["product_id"]) in candidates
        }

    # 2. Content-based TF-IDF similarity scores
    cb_scores = {}

    if content_model.similarity_matrix is not None:
        product_to_row = {
            pid: index for index, pid in enumerate(product_ids)
        }

        seen_rows = [
            product_to_row[pid]
            for pid in seen
            if pid in product_to_row
        ]

        if seen_rows:
            for pid in candidates:
                target_row = product_to_row[pid]

                cb_scores[pid] = max(
                    float(content_model.similarity_matrix[
                        source_row, target_row
                    ])
                    for source_row in seen_rows
                )

    # 3. NCF scores
    ncf_scores = {}

    if ncf_user_index is not None:
        ncf_results = ncf_recommend(
            ncf_user_index,
            top_k=len(product_ids)
        )

        ncf_scores = {
            int(item["product_id"]): float(item["ncf_score"])
            for item in ncf_results
            if int(item["product_id"]) in candidates
        }

    # 4. Normalize individual models
    svd_norm = normalize(svd_scores)
    cb_norm = normalize(cb_scores)
    ncf_norm = normalize(ncf_scores)

    # 5. Weighted hybrid score
    recommendations = []

    for pid in candidates:
        # Missing collaborative scores indicate an untrained item,
        # not a negative preference. Renormalize available model weights.
        signals = [(weight, scores[pid]) for weight, scores in (
            (0.3, svd_norm), (0.3, cb_norm), (0.4, ncf_norm)
        ) if pid in scores]
        if not signals:
            continue
        score = sum(w * s for w, s in signals) / sum(w for w, _ in signals)

        recommendations.append({
            "product_id": pid,
            "hybrid_score": round(score, 4)
        })

    recommendations.sort(
        key=lambda item: item["hybrid_score"],
        reverse=True
    )

    # Return an empty list when no model has a signal.
    if not (svd_scores or cb_scores or ncf_scores):
        return []

    return recommendations[:top_k]
