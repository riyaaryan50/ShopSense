
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models import Product

product_bp = Blueprint(
    "products",
    __name__,
    url_prefix="/api/products"
)


# Convert product object into JSON
def product_to_dict(product):
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "price": float(product.price),
        "stock": product.stock,
        "image_url": product.image_url
    }


# 1. GET ALL PRODUCTS
@product_bp.route("/", methods=["GET"])
def get_products():

    products = Product.query.all()

    return jsonify([
        product_to_dict(product)
        for product in products
    ]), 200


# 2. GET PRODUCT BY ID
@product_bp.route("/<int:product_id>", methods=["GET"])
def get_product(product_id):

    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(product_to_dict(product)), 200


# 3. CREATE PRODUCT
@product_bp.route("/", methods=["POST"])
@jwt_required()
def create_product():

    data = request.get_json(silent=True) or {}

    required_fields = ["name", "price"]

    for field in required_fields:
        if field not in data or data[field] is None:
            return jsonify({
                "error": f"{field} is required"
            }), 400

    try:
        price = float(data["price"])
        stock = int(data.get("stock", 0))

        if not data["name"].strip():
            return jsonify({"error": "Name cannot be empty"}), 400

        if price < 0 or stock < 0:
            return jsonify({
                "error": "Price and stock cannot be negative"
            }), 400

        product = Product(
            name=data["name"].strip(),
            description=data.get("description"),
            category=data.get("category"),
            price=price,
            stock=stock,
            image_url=data.get("image_url")
        )

        db.session.add(product)
        db.session.commit()

        return jsonify({
            "message": "Product created successfully",
            "product": product_to_dict(product)
        }), 201

    except (ValueError, TypeError):
        db.session.rollback()
        return jsonify({"error": "Invalid price or stock"}), 400

    except Exception:
        db.session.rollback()
        raise


# 4. UPDATE PRODUCT
@product_bp.route("/<int:product_id>", methods=["PUT"])
@jwt_required()
def update_product(product_id):

    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify({"error": "Valid JSON data required"}), 400

    try:
        if "name" in data:
            if not isinstance(data["name"], str) or not data["name"].strip():
                return jsonify({"error": "Invalid product name"}), 400
            product.name = data["name"].strip()

        if "description" in data:
            product.description = data["description"]

        if "category" in data:
            product.category = data["category"]

        if "price" in data:
            price = float(data["price"])
            if price < 0:
                return jsonify({"error": "Price cannot be negative"}), 400
            product.price = price

        if "stock" in data:
            stock = int(data["stock"])
            if stock < 0:
                return jsonify({"error": "Stock cannot be negative"}), 400
            product.stock = stock

        if "image_url" in data:
            product.image_url = data["image_url"]

        db.session.commit()

        return jsonify({
            "message": "Product updated successfully",
            "product": product_to_dict(product)
        }), 200

    except (ValueError, TypeError):
        db.session.rollback()
        return jsonify({"error": "Invalid price or stock"}), 400

    except Exception:
        db.session.rollback()
        raise


# 5. DELETE PRODUCT
@product_bp.route("/<int:product_id>", methods=["DELETE"])
@jwt_required()
def delete_product(product_id):

    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()

    return jsonify({
        "message": "Product deleted successfully"
    }), 200
