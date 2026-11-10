
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Review, Product

review_bp = Blueprint(
    "reviews",
    __name__,
    url_prefix="/api/reviews"
)


def review_to_dict(review):
    return {
        "id": review.id,
        "user_id": review.user_id,
        "product_id": review.product_id,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": (
            review.created_at.isoformat()
            if review.created_at else None
        )
    }


# 1. SUBMIT REVIEW
@review_bp.route("/", methods=["POST"])
@jwt_required()
def create_review():

    data = request.get_json(silent=True) or {}

    product_id = data.get("product_id")
    rating = data.get("rating")
    comment = data.get("comment", "")

    if product_id is None or rating is None:
        return jsonify({
            "error": "Product ID and rating are required"
        }), 400

    try:
        product_id = int(product_id)
        rating = int(rating)

        if product_id <= 0:
            return jsonify({"error": "Invalid product ID"}), 400

        if rating < 1 or rating > 5:
            return jsonify({
                "error": "Rating must be between 1 and 5"
            }), 400

    except (ValueError, TypeError):
        return jsonify({"error": "Invalid product ID or rating"}), 400

    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    user_id = int(get_jwt_identity())

    existing_review = Review.query.filter_by(
        user_id=user_id,
        product_id=product_id
    ).first()

    if existing_review:
        return jsonify({
            "error": "You have already reviewed this product"
        }), 409

    review = Review(
        user_id=user_id,
        product_id=product_id,
        rating=rating,
        comment=comment
    )

    db.session.add(review)
    db.session.commit()

    return jsonify({
        "message": "Review submitted successfully",
        "review": review_to_dict(review)
    }), 201


# 2. GET REVIEWS FOR A PRODUCT
@review_bp.route("/product/<int:product_id>", methods=["GET"])
def get_product_reviews(product_id):

    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    reviews = Review.query.filter_by(
        product_id=product_id
    ).order_by(Review.created_at.desc()).all()

    return jsonify({
        "product_id": product_id,
        "total_reviews": len(reviews),
        "reviews": [
            review_to_dict(review) for review in reviews
        ]
    }), 200


# 3. GET LOGGED-IN USER'S REVIEWS
@review_bp.route("/my-reviews", methods=["GET"])
@jwt_required()
def get_my_reviews():

    user_id = int(get_jwt_identity())

    reviews = Review.query.filter_by(
        user_id=user_id
    ).order_by(Review.created_at.desc()).all()

    return jsonify({
        "total_reviews": len(reviews),
        "reviews": [
            review_to_dict(review) for review in reviews
        ]
    }), 200
