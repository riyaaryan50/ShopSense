"""Gateway routes that proxy the AI microservices (sprint plan, Member 2 Day 4).

POST /api/search/semantic                -> NLP service (falls back to keyword search)
GET  /api/reviews/<id>/summary           -> NLP service review sentiment summary
GET  /api/similar/<product_id>           -> content-based (5001) or NLP embeddings
GET  /api/recommendations/popular        -> popularity baseline (cold start)
GET  /api/recommendations/me             -> blended personal recommendations (JWT)
GET  /api/recommendations/<user_id>      -> same, for the logged-in user only (JWT)
"""

from collections import defaultdict

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func

from app.ai_clients import ServiceUnavailable, call, cb_url, ml_url, nlp_url
from app import cache
from app.extensions import db
from app.models import Interaction, Product, Review
from app.routes.product import keyword_filter, product_to_dict
from app.routes.survey import latest_survey, purchased_or_in_cart, survey_recommendations

ai_bp = Blueprint("ai", __name__, url_prefix="/api")

EVENT_WEIGHTS = {"view": 1.0, "click": 1.5, "wishlist": 2.5, "cart": 3.0, "purchase": 5.0}

# Weight of each recommendation source in the blend.
SOURCE_WEIGHTS = {"hybrid": 0.45, "content": 0.30, "survey": 0.35, "popular": 0.10}
SOURCE_REASONS = {
    "hybrid": "People with similar taste liked this",
    "content": "Similar to products you've interacted with",
    "survey": "Matches your survey preferences",
    "popular": "Popular with other shoppers",
}


def _limit(default=10, high=50):
    value = request.args.get("limit", default=default, type=int) or default
    return max(1, min(value, high))


def _products_by_id(ids):
    if not ids:
        return {}
    return {p.id: p for p in Product.query.filter(Product.id.in_(list(ids))).all()}


# ---------------------------------------------------------------------- #
# Semantic search + review summary + similar products
# ---------------------------------------------------------------------- #
@ai_bp.route("/search/semantic", methods=["POST"])
def semantic_search():
    body = request.get_json(silent=True) or {}
    query = str(body.get("query") or "").strip()
    if not query:
        return jsonify({"error": "query is required"}), 400
    top_k = max(1, min(int(body.get("top_k", 10)), 50))

    try:
        status, data = call("POST", nlp_url(), "/api/nlp/search", json={
            "query": query, "top_k": top_k,
            "category": body.get("category"),
            "min_price": body.get("min_price"), "max_price": body.get("max_price"),
            "min_score": body.get("min_score"),
        })
        if status == 200:
            scores = dict(zip(data.get("product_ids", []), data.get("scores", [])))
            products = _products_by_id(scores)
            return jsonify({
                "query": query,
                "engine": data.get("engine"),
                "latency_ms": data.get("latency_ms"),
                "results": [
                    {**product_to_dict(products[pid]), "score": scores[pid]}
                    for pid in data.get("product_ids", []) if pid in products
                ],
            }), 200
    except ServiceUnavailable:
        pass

    products = keyword_filter(Product.query, query).limit(top_k).all()
    return jsonify({
        "query": query,
        "engine": "keyword-fallback",
        "results": [product_to_dict(p) for p in products],
    }), 200


@ai_bp.route("/reviews/<int:product_id>/summary", methods=["GET"])
def review_summary(product_id):
    if not db.session.get(Product, product_id):
        return jsonify({"error": "Product not found"}), 404
    params = {k: v for k, v in request.args.items() if k in ("include_reviews", "fresh")}
    try:
        status, data = call("GET", nlp_url(),
                            f"/api/nlp/reviews/{product_id}/summary", params=params)
        return jsonify(data), status
    except ServiceUnavailable:
        return jsonify({"error": "Review analysis service is unavailable"}), 503


@ai_bp.route("/similar/<int:product_id>", methods=["GET"])
def similar_products(product_id):
    if not db.session.get(Product, product_id):
        return jsonify({"error": "Product not found"}), 404
    top_k = _limit(default=5, high=20)

    ids, source = [], None
    try:
        status, data = call("GET", cb_url(), f"/api/recommendations/{product_id}")
        if status == 200 and data.get("recommendations"):
            ids = [int(r["id"]) for r in data["recommendations"]][:top_k]
            source = "content-based (TF-IDF)"
    except ServiceUnavailable:
        pass

    if not ids:
        try:
            status, data = call("GET", nlp_url(), f"/api/nlp/similar/{product_id}",
                                params={"top_k": top_k})
            if status == 200:
                ids = [int(r["id"]) for r in data.get("recommendations", [])]
                source = f"semantic embeddings ({data.get('engine')})"
        except ServiceUnavailable:
            pass

    if not ids:
        product = db.session.get(Product, product_id)
        ids = [p.id for p in Product.query.filter(
            Product.category == product.category, Product.id != product_id
        ).limit(top_k).all()]
        source = "same-category fallback"

    products = _products_by_id(ids)
    return jsonify({
        "product_id": product_id,
        "source": source,
        "recommendations": [product_to_dict(products[i]) for i in ids if i in products],
    }), 200


# ---------------------------------------------------------------------- #
# Recommendations
# ---------------------------------------------------------------------- #
def popularity_scores():
    """Weighted interaction counts + review counts per product."""
    scores = defaultdict(float)
    rows = (db.session.query(Interaction.product_id, Interaction.event_type,
                             func.count(Interaction.id))
            .group_by(Interaction.product_id, Interaction.event_type).all())
    for product_id, event_type, count in rows:
        scores[product_id] += EVENT_WEIGHTS.get(event_type, 1.0) * count

    rows = (db.session.query(Review.product_id, func.avg(Review.rating), func.count(Review.id))
            .group_by(Review.product_id).all())
    for product_id, avg_rating, count in rows:
        scores[product_id] += float(avg_rating or 0) * count * 0.5
    return dict(scores)


@ai_bp.route("/recommendations/popular", methods=["GET"])
def popular():
    limit = _limit()
    scores = popularity_scores()
    ranked = sorted(scores, key=scores.get, reverse=True)[:limit]
    products = _products_by_id(ranked)
    return jsonify({
        "algorithm": "popularity-baseline",
        "recommendations": [
            {**product_to_dict(products[pid]), "score": round(scores[pid], 2),
             "reason": SOURCE_REASONS["popular"]}
            for pid in ranked if pid in products
        ],
    }), 200


def _normalise(scores):
    if not scores:
        return {}
    low, high = min(scores.values()), max(scores.values())
    if high - low < 1e-9:
        return {k: 1.0 for k in scores}
    return {k: (v - low) / (high - low) for k, v in scores.items()}


def _collect_sources(user_id, token, exclude):
    sources, reasons = {}, {}

    # 1. Hybrid NCF + SVD + TF-IDF engine (Member 3), when deployed.
    try:
        status, data = call("GET", ml_url(), f"/recommend/{user_id}", params={"top_k": 20})
        if status == 200:
            sources["hybrid"] = {int(r["product_id"]): float(r["hybrid_score"])
                                 for r in data.get("recommendations", [])}
    except (ServiceUnavailable, KeyError, TypeError, ValueError):
        pass

    # 2. Content-based personalised model (Member 1) – uses interaction history.
    try:
        status, data = call("GET", cb_url(), f"/api/personalized/{user_id}",
                            headers={"Authorization": f"Bearer {token}"})
        if status == 200 and data.get("recommendations"):
            sources["content"] = {int(r["id"]): float(r.get("recommendation_score", 0))
                                  for r in data["recommendations"]}
    except (ServiceUnavailable, KeyError, TypeError, ValueError):
        pass

    # 3. Survey answers (NLP service – semantic match of stated needs).
    survey = latest_survey(user_id)
    if survey:
        recs, _engine = survey_recommendations(survey.answers, exclude, top_k=20)
        sources["survey"] = {int(r["product_id"]): float(r["match_score"]) for r in recs}
        for r in recs:
            if r.get("reasons"):
                reasons[int(r["product_id"])] = r["reasons"][0]

    # 4. Popularity baseline – weak prior + cold-start fallback.
    sources["popular"] = popularity_scores()

    return {name: {pid: s for pid, s in scores.items() if pid not in exclude}
            for name, scores in sources.items()}, reasons, survey is not None


def _explanation(used, has_survey):
    labels = {
        "hybrid": "the hybrid NCF model",
        "content": "your browsing history",
        "survey": "your survey answers",
    }
    personal = [labels[s] for s in ("hybrid", "content", "survey") if s in used]
    if not personal:
        return ("We don't know your taste yet, so these are popular products. "
                + ("" if has_survey else "Take the survey for personalised picks!"))
    return "Picked for you using " + " and ".join(personal) + "."


def blended_recommendations(user_id, token, limit):
    exclude = purchased_or_in_cart(user_id)
    sources, survey_reasons, has_survey = _collect_sources(user_id, token, exclude)
    personal = [s for s in ("hybrid", "content", "survey") if sources.get(s)]
    used = personal + ["popular"]

    normalised = {name: _normalise(sources.get(name, {})) for name in used}
    total_weight = sum(SOURCE_WEIGHTS[name] for name in used)

    combined = defaultdict(float)
    contributions = defaultdict(dict)
    for name in used:
        for pid, value in normalised[name].items():
            part = SOURCE_WEIGHTS[name] * value / total_weight
            combined[pid] += part
            contributions[pid][name] = round(part, 4)

    ranked = sorted(combined, key=combined.get, reverse=True)[:limit]
    products = _products_by_id(ranked)

    results = []
    for pid in ranked:
        if pid not in products:
            continue
        parts = contributions[pid]
        main = max(parts, key=parts.get)
        reason = survey_reasons.get(pid) if main == "survey" else None
        results.append({
            **product_to_dict(products[pid]),
            "score": round(combined[pid], 4),
            "sources": sorted(parts, key=parts.get, reverse=True),
            "reason": reason or SOURCE_REASONS[main],
        })

    return {
        "user_id": user_id,
        "sources_used": used,
        "cold_start": not personal,
        "has_survey": has_survey,
        "explanation": _explanation(used, has_survey),
        "recommendations": results,
    }


def _token():
    header = request.headers.get("Authorization", "")
    return header.split(" ", 1)[1] if header.startswith("Bearer ") else ""


CACHED_LIMIT = 50


def cached_recommendations(user_id, limit):
    """Blended recommendations, served from the user:{id}:recs cache when fresh."""
    payload = cache.get_recs(user_id)
    cached = payload is not None
    if not cached:
        payload = blended_recommendations(user_id, _token(), CACHED_LIMIT)
        cache.set_recs(user_id, payload)
    return {**payload, "recommendations": payload["recommendations"][:limit],
            "cached": cached, "cache_backend": cache.BACKEND}


@ai_bp.route("/recommendations/me", methods=["GET"])
@jwt_required()
def my_recommendations():
    user_id = int(get_jwt_identity())
    return jsonify(cached_recommendations(user_id, _limit())), 200


@ai_bp.route("/recommendations/<int:user_id>", methods=["GET"])
@jwt_required()
def user_recommendations(user_id):
    if user_id != int(get_jwt_identity()):
        return jsonify({"error": "You can only view your own recommendations"}), 403
    return jsonify(cached_recommendations(user_id, _limit())), 200
