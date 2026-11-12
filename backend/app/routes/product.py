
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
        "image_url": product.image_url,
        "brand": product.brand,
        "original_price": (
            float(product.original_price)
            if product.original_price is not None else None
        ),
        "marketplace": product.marketplace,
        "product_url": product.product_url,
        "specifications": product.specifications or {},
        "marketplace_links": product.marketplace_links or {}
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
        if not isinstance(data["name"], str) or not data["name"].strip():
            return jsonify({"error": "Name cannot be empty"}), 400

        price = float(data["price"])
        stock = int(data.get("stock", 0))

        original_price = (
            float(data["original_price"])
            if data.get("original_price") is not None else None
        )

        specifications = data.get("specifications") or {}
        marketplace_links = data.get("marketplace_links") or {}

        if price < 0 or stock < 0 or (
            original_price is not None and original_price < 0
        ):
            return jsonify({
                "error": "Prices and stock cannot be negative"
            }), 400

        if not isinstance(specifications, dict):
            return jsonify({
                "error": "Specifications must be a JSON object"
            }), 400

        if not isinstance(marketplace_links, dict):
            return jsonify({
                "error": "Marketplace links must be a JSON object"
            }), 400

        product = Product(
            name=data["name"].strip(),
            description=data.get("description"),
            category=data.get("category"),
            price=price,
            stock=stock,
            image_url=data.get("image_url"),
            brand=data.get("brand"),
            original_price=original_price,
            marketplace=data.get("marketplace"),
            product_url=data.get("product_url"),
            specifications=specifications,
            marketplace_links=marketplace_links
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

        if "brand" in data:
            product.brand = data["brand"]

        if "original_price" in data:
            original_price = (
                float(data["original_price"])
                if data["original_price"] is not None else None
            )
            if original_price is not None and original_price < 0:
                return jsonify({"error": "Original price cannot be negative"}), 400
            product.original_price = original_price

        if "marketplace" in data:
            product.marketplace = data["marketplace"]

        if "product_url" in data:
            product.product_url = data["product_url"]

        if "specifications" in data:
            if not isinstance(data["specifications"], dict):
                return jsonify({
                    "error": "Specifications must be a JSON object"
                }), 400
            product.specifications = data["specifications"]

        if "marketplace_links" in data:
            if not isinstance(data["marketplace_links"], dict):
                return jsonify({
                    "error": "Marketplace links must be a JSON object"
                }), 400
            product.marketplace_links = data["marketplace_links"]

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
