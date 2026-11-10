
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import CartItem, Product

cart_bp = Blueprint(
    "cart",
    __name__,
    url_prefix="/api/cart"
)


# Convert cart item into JSON

def cart_item_to_dict(item):

    # Fetch product using its foreign key
    product = db.session.get(Product, item.product_id)

    return {
        "cart_item_id": item.id,
        "product_id": item.product_id,
        "product_name": product.name,
        "price": float(product.price),
        "quantity": item.quantity,
        "subtotal": float(product.price * item.quantity)
    }



# 1. ADD PRODUCT TO CART
@cart_bp.route("/", methods=["POST"])
@jwt_required()
def add_to_cart():

    data = request.get_json(silent=True) or {}

    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    try:
        product_id = int(product_id)
        quantity = int(quantity)

        if product_id <= 0 or quantity <= 0:
            return jsonify({
                "error": "Product ID and quantity must be positive"
            }), 400

    except (ValueError, TypeError):
        return jsonify({
            "error": "Valid product ID and quantity are required"
        }), 400

    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    if quantity > product.stock:
        return jsonify({
            "error": "Requested quantity exceeds available stock"
        }), 400

    user_id = int(get_jwt_identity())

    cart_item = CartItem.query.filter_by(
        user_id=user_id,
        product_id=product_id
    ).first()

    if cart_item:
        new_quantity = cart_item.quantity + quantity

        if new_quantity > product.stock:
            return jsonify({
                "error": "Requested quantity exceeds available stock"
            }), 400

        cart_item.quantity = new_quantity

    else:
        cart_item = CartItem(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)

    db.session.commit()

    return jsonify({
        "message": "Product added to cart successfully",
        "cart_item": cart_item_to_dict(cart_item)
    }), 201


# 2. VIEW CART
@cart_bp.route("/", methods=["GET"])
@jwt_required()
def get_cart():

    user_id = int(get_jwt_identity())

    cart_items = CartItem.query.filter_by(
        user_id=user_id
    ).all()

    items = [
        cart_item_to_dict(item)
        for item in cart_items
    ]

    total_price = sum(
        item["subtotal"] for item in items
    )

    total_quantity = sum(
        item["quantity"] for item in items
    )

    return jsonify({
        "items": items,
        "total_items": len(items),
        "total_quantity": total_quantity,
        "total_price": round(total_price, 2)
    }), 200


# 3. UPDATE CART QUANTITY
@cart_bp.route("/<int:cart_item_id>", methods=["PUT"])
@jwt_required()
def update_cart_item(cart_item_id):

    user_id = int(get_jwt_identity())

    cart_item = CartItem.query.filter_by(
        id=cart_item_id,
        user_id=user_id
    ).first()

    if not cart_item:
        return jsonify({"error": "Cart item not found"}), 404

    data = request.get_json(silent=True) or {}

    try:
        quantity = int(data.get("quantity"))

        if quantity <= 0:
            return jsonify({
                "error": "Quantity must be greater than zero"
            }), 400

    except (ValueError, TypeError):
        return jsonify({"error": "Valid quantity is required"}), 400

    product = db.session.get(Product, cart_item.product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    if quantity > product.stock:
        return jsonify({
           "error": "Requested quantity exceeds available stock"
        }), 400

    cart_item.quantity = quantity
    db.session.commit()

    return jsonify({
        "message": "Cart quantity updated successfully",
        "cart_item": cart_item_to_dict(cart_item)
    }), 200


# 4. REMOVE ITEM FROM CART
@cart_bp.route("/<int:cart_item_id>", methods=["DELETE"])
@jwt_required()
def remove_from_cart(cart_item_id):

    user_id = int(get_jwt_identity())

    cart_item = CartItem.query.filter_by(
        id=cart_item_id,
        user_id=user_id
    ).first()

    if not cart_item:
        return jsonify({"error": "Cart item not found"}), 404

    db.session.delete(cart_item)
    db.session.commit()

    return jsonify({
        "message": "Product removed from cart successfully"
    }), 200
