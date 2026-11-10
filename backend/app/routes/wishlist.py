
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import WishlistItem, Product

wishlist_bp = Blueprint(
    "wishlist",
    __name__,
    url_prefix="/api/wishlist"
)


# Convert wishlist item into JSON
def wishlist_item_to_dict(item):

    product = db.session.get(Product, item.product_id)

    if not product:
        return {
            "wishlist_item_id": item.id,
            "product_id": item.product_id,
            "product": None
        }

    return {
        "wishlist_item_id": item.id,
        "product_id": item.product_id,
        "product_name": product.name,
        "price": float(product.price)
    }


# 1. ADD PRODUCT TO WISHLIST
@wishlist_bp.route("/", methods=["POST"])
@jwt_required()
def add_to_wishlist():

    data = request.get_json(silent=True) or {}

    product_id = data.get("product_id")

    try:
        product_id = int(product_id)

        if product_id <= 0:
            return jsonify({"error": "Invalid product ID"}), 400

    except (ValueError, TypeError):
        return jsonify({"error": "Valid product ID is required"}), 400

    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    user_id = int(get_jwt_identity())

    existing_item = WishlistItem.query.filter_by(
        user_id=user_id,
        product_id=product_id
    ).first()

    if existing_item:
        return jsonify({
            "error": "Product already exists in wishlist"
        }), 409

    wishlist_item = WishlistItem(
        user_id=user_id,
        product_id=product_id
    )

    db.session.add(wishlist_item)
    db.session.commit()

    return jsonify({
        "message": "Product added to wishlist successfully",
        "wishlist_item": wishlist_item_to_dict(wishlist_item)
    }), 201


# 2. VIEW MY WISHLIST
@wishlist_bp.route("/", methods=["GET"])
@jwt_required()
def get_wishlist():

    user_id = int(get_jwt_identity())

    wishlist_items = WishlistItem.query.filter_by(
        user_id=user_id
    ).all()

    items = [
        wishlist_item_to_dict(item)
        for item in wishlist_items
    ]

    return jsonify({
        "total_items": len(items),
        "wishlist": items
    }), 200


# 3. REMOVE PRODUCT FROM WISHLIST
@wishlist_bp.route("/<int:wishlist_item_id>", methods=["DELETE"])
@jwt_required()
def remove_from_wishlist(wishlist_item_id):

    user_id = int(get_jwt_identity())

    wishlist_item = WishlistItem.query.filter_by(
        id=wishlist_item_id,
        user_id=user_id
    ).first()

    if not wishlist_item:
        return jsonify({
            "error": "Wishlist item not found"
        }), 404

    db.session.delete(wishlist_item)
    db.session.commit()

    return jsonify({
        "message": "Product removed from wishlist successfully"
    }), 200
