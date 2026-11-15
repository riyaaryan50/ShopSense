"""Onboarding preference survey.

POST /api/survey/                    save answers (JWT)
GET  /api/survey/                    latest answers of the current user (JWT)
POST /api/survey/recommendations     survey-based recommendations
                                     - logged in: uses saved answers unless
                                       "answers" is sent in the body
                                     - guest: "answers" must be in the body
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.ai_clients import ServiceUnavailable, call, nlp_url
from app.extensions import db
from app.cache import invalidate_recs
from app.models import CartItem, Interaction, Product, SurveyResponse
from app.routes.product import product_to_dict

survey_bp = Blueprint("survey", __name__, url_prefix="/api/survey")

ALLOWED_KEYS = {
    "role", "interests", "uses", "budget_min", "budget_max",
    "priorities", "brands", "description",
}
LIST_KEYS = {"interests", "uses", "priorities", "brands"}


def clean_answers(raw):
    if not isinstance(raw, dict):
        raise ValueError("answers must be a JSON object")

    answers = {}
    for key in ALLOWED_KEYS:
        value = raw.get(key)
        if value in (None, ""):
            continue
        if key in LIST_KEYS:
            if not isinstance(value, list):
                raise ValueError(f"{key} must be a list")
            answers[key] = [str(v)[:60] for v in value][:15]
        elif key in ("budget_min", "budget_max"):
            number = float(value)
            if number < 0:
                raise ValueError("budget cannot be negative")
            answers[key] = number
        else:
            answers[key] = str(value)[:500]

    if not answers.get("interests") and not answers.get("uses") \
            and not answers.get("description"):
        raise ValueError(
            "Choose at least one interest or use, or describe what you need"
        )
    return answers


def latest_survey(user_id):
    return (
        SurveyResponse.query
        .filter_by(user_id=user_id)
        .order_by(SurveyResponse.created_at.desc(), SurveyResponse.id.desc())
        .first()
    )


def purchased_or_in_cart(user_id):
    purchased = {
        row.product_id for row in
        Interaction.query.filter_by(user_id=user_id, event_type="purchase").all()
    }
    in_cart = {row.product_id for row in CartItem.query.filter_by(user_id=user_id).all()}
    return purchased | in_cart


def rule_based_survey_recs(answers, exclude_ids, top_k):
    """Fallback when the NLP service is down: category + budget filter."""
    interests = set(answers.get("interests") or [])
    budget = answers.get("budget_max")
    results = []
    for product in Product.query.order_by(Product.price).all():
        if product.id in exclude_ids:
            continue
        reasons = []
        score = 0.0
        if product.category in interests:
            score += 0.6
            reasons.append(f"Matches your interest in {product.category}")
        if budget and float(product.price) <= budget:
            score += 0.4
            reasons.append(f"Within your ₹{budget:,.0f} budget")
        if score > 0:
            results.append({
                "product_id": product.id,
                "match_score": round(score * 100, 1),
                "reasons": reasons,
            })
    results.sort(key=lambda r: r["match_score"], reverse=True)
    return results[:top_k]


def survey_recommendations(answers, exclude_ids=(), top_k=8):
    """Returns (recommendations, engine). Each item has product_id, match_score, reasons."""
    try:
        status, data = call(
            "POST", nlp_url(), "/api/nlp/survey/recommend",
            json={"answers": answers, "top_k": top_k, "exclude_ids": list(exclude_ids)},
        )
        if status == 200:
            return data.get("recommendations", []), data.get("engine", "nlp-service")
    except ServiceUnavailable:
        pass
    return rule_based_survey_recs(answers, set(exclude_ids), top_k), "rule-based-fallback"


# ---------------------------------------------------------------------- #
@survey_bp.route("/", methods=["POST"])
@jwt_required()
def save_survey():
    data = request.get_json(silent=True) or {}
    try:
        answers = clean_answers(data.get("answers", data))
    except (ValueError, TypeError) as error:
        return jsonify({"error": str(error)}), 400

    user_id = int(get_jwt_identity())
    response = SurveyResponse(user_id=user_id, answers=answers)
    db.session.add(response)
    db.session.commit()
    invalidate_recs(user_id)

    return jsonify({
        "message": "Survey saved",
        "survey": {"id": response.id, "answers": response.answers},
    }), 201


@survey_bp.route("/", methods=["GET"])
@jwt_required()
def get_survey():
    survey = latest_survey(int(get_jwt_identity()))
    if not survey:
        return jsonify({"error": "No survey submitted yet"}), 404
    return jsonify({
        "id": survey.id,
        "answers": survey.answers,
        "created_at": survey.created_at.isoformat() if survey.created_at else None,
    }), 200


@survey_bp.route("/recommendations", methods=["POST"])
@jwt_required(optional=True)
def recommend_from_survey():
    data = request.get_json(silent=True) or {}
    identity = get_jwt_identity()
    user_id = int(identity) if identity else None

    if data.get("answers") is not None:
        try:
            answers = clean_answers(data["answers"])
        except (ValueError, TypeError) as error:
            return jsonify({"error": str(error)}), 400
    elif user_id:
        survey = latest_survey(user_id)
        if not survey:
            return jsonify({"error": "No survey submitted yet"}), 404
        answers = survey.answers
    else:
        return jsonify({"error": "answers are required for guests"}), 400

    top_k = max(1, min(int(data.get("top_k", 8)), 20))
    exclude = purchased_or_in_cart(user_id) if user_id else set()
    recs, engine = survey_recommendations(answers, exclude, top_k)

    products = {p.id: p for p in Product.query.filter(
        Product.id.in_([r["product_id"] for r in recs])).all()}

    return jsonify({
        "answers": answers,
        "engine": engine,
        "recommendations": [
            {
                **product_to_dict(products[r["product_id"]]),
                "match_score": r.get("match_score"),
                "reasons": r.get("reasons", []),
                "breakdown": r.get("breakdown"),
            }
            for r in recs if r["product_id"] in products
        ],
    }), 200
