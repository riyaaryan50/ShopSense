
from flask import Flask, jsonify
from flask_cors import CORS

from recommender import ProductRecommender

app = Flask(__name__)
CORS(app)

# Initialize the recommendation model
recommender = ProductRecommender()

# Load products and build the model when the API starts
if recommender.load_products():
    recommender.build_model()
else:
    print("Warning: Could not load products from backend.")


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "ShopSense Recommendation API",
        "status": "running"
    }), 200


@app.route("/api/recommendations/<int:product_id>", methods=["GET"])
def get_recommendations(product_id):

    if recommender.products is None or recommender.similarity_matrix is None:
        return jsonify({
            "error": "Recommendation model is not available"
        }), 503

    recommendations = recommender.recommend(
        product_id=product_id,
        top_n=5
    )

    if not recommendations:
        return jsonify({
            "message": "No recommendations found",
            "recommendations": []
        }), 404

    return jsonify({
        "product_id": product_id,
        "recommendations": recommendations
    }), 200


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True
    )
