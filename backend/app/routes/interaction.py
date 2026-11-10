
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Interaction, Product

interaction_bp = Blueprint(
    "interaction",
    __name__,
    url_prefix="/api/interactions"
)

# Allowed customer activities
ALLOWED_EVENTS = {
    "view",
    "click",
    "cart",
    "wishlist",
    "purchase"
}


# Convert interaction into JSON
def interaction_to_dict(interaction):

    return {
        "id": interaction.id,
        "user_id": interaction.user_id,
        "product_id": interaction.product_id,
        "event_type": interaction.event_type,
        "created_at": (
            interaction.created_at.isoformat()
            if interaction.created_at else None
        )
    }


# 1. RECORD USER INTERACTION
@interaction_bp.route("/", methods=["POST"])
@jwt_required()
def record_interaction():

    data = request.get_json(silent=True) or {}

    product_id = data.get("product_id")
    event_type = data.get("event_type")

    if not product_id or not event_type:
        return jsonify({
            "error": "product_id and event_type are required"
        }), 400

    try:
        product_id = int(product_id)

        if product_id <= 0:
            return jsonify({
                "error": "Invalid product ID"
            }), 400

    except (ValueError, TypeError):
        return jsonify({
            "error": "Valid product ID is required"
        }), 400

    if not isinstance(event_type, str):
        return jsonify({
            "error": "Invalid event type"
        }), 400

    event_type = event_type.strip().lower()

    if event_type not in ALLOWED_EVENTS:
        return jsonify({
            "error": "Invalid event type",
            "allowed_events": sorted(ALLOWED_EVENTS)
        }), 400

    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({
            "error": "Product not found"
        }), 404

    user_id = int(get_jwt_identity())

    interaction = Interaction(
        user_id=user_id,
        product_id=product_id,
        event_type=event_type
    )

    db.session.add(interaction)
    db.session.commit()

    return jsonify({
        "message": "Interaction recorded successfully",
        "interaction": interaction_to_dict(interaction)
    }), 201


# 2. GET MY INTERACTION HISTORY
@interaction_bp.route("/", methods=["GET"])
@jwt_required()
def get_my_interactions():

    user_id = int(get_jwt_identity())

    interactions = Interaction.query.filter_by(
        user_id=user_id
    ).order_by(
        Interaction.created_at.desc()
    ).all()

    return jsonify({
        "total_interactions": len(interactions),
        "interactions": [
            interaction_to_dict(item)
            for item in interactions
        ]
    }), 200


# 3. GET INTERACTIONS FOR A PRODUCT
@interaction_bp.route("/product/<int:product_id>", methods=["GET"])
@jwt_required()
def get_product_interactions(product_id):

    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({
            "error": "Product not found"
        }), 404

    interactions = Interaction.query.filter_by(
        product_id=product_id
    ).order_by(
        Interaction.created_at.desc()
    ).all()

    return jsonify({
        "product_id": product_id,
        "total_interactions": len(interactions),
        "interactions": [
            interaction_to_dict(item)
            for item in interactions
        ]
    }), 200
