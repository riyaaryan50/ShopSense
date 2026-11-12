
import os
import pickle

import numpy as np

from flask import Flask, jsonify, request
from flask_cors import CORS

from recommender import ProductRecommender


app = Flask(__name__)
CORS(app)


# ==========================================
# CONTENT-BASED RECOMMENDATION MODEL
# ==========================================

recommender = ProductRecommender()

if recommender.load_products():
    recommender.build_model()
else:
    print("Warning: Could not load products from backend.")


# ==========================================
# LOAD SVD COLLABORATIVE MODEL
# ==========================================

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "svd_model.pkl"
)

svd_model = None

try:
    with open(MODEL_PATH, "rb") as file:
        svd_model = pickle.load(file)

    print("SVD collaborative model loaded successfully.")

except Exception as error:
    print("SVD model loading error:", error)


# ==========================================
# HOME API
# ==========================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message": "ShopSense Recommendation API",
        "status": "running",
        "content_based": recommender.products is not None,
        "collaborative_filtering": svd_model is not None
    }), 200


# ==========================================
# SIMILAR PRODUCTS API
# ==========================================

@app.route("/api/recommendations/<int:product_id>", methods=["GET"])
def get_recommendations(product_id):

    if (
        recommender.products is None
        or recommender.similarity_matrix is None
    ):
        return jsonify({
            "error": "Recommendation model is not available"
        }), 503

    recommendations = recommender.recommend(
        product_id=product_id,
        top_n=5
    )

    return jsonify({
        "product_id": product_id,
        "recommendations": recommendations
    }), 200


# ==========================================
# PERSONALIZED CONTENT-BASED API
# ==========================================

@app.route("/api/personalized/<int:user_id>", methods=["GET"])
def personalized_recommendations(user_id):

    if (
        recommender.products is None
        or recommender.tfidf_matrix is None
    ):
        return jsonify({
            "error": "Recommendation model is not available"
        }), 503

    token = request.headers.get("Authorization", "")

    if not token.startswith("Bearer "):
        return jsonify({
            "error": "Authentication token required"
        }), 401

    try:

        weight_mode = request.args.get(
            "weight_mode",
            default="fuzzy"
        ).lower()

        if weight_mode not in ("fixed", "fuzzy"):
            return jsonify({
                "error": "weight_mode must be 'fixed' or 'fuzzy'"
            }), 400

        recommendations = recommender.recommend_for_user(
            user_id=user_id,
            token=token.split(" ", 1)[1],
            top_n=5,
            weight_mode=weight_mode
        )

        return jsonify({
            "user_id": user_id,
            "recommendations": recommendations
        }), 200

    except Exception as error:

        print("Personalized recommendation error:", error)

        return jsonify({
            "error": "Could not generate personalized recommendations"
        }), 500


# ==========================================
# SVD COLLABORATIVE FILTERING API
# ==========================================

@app.route("/api/collaborative/<int:user_id>", methods=["GET"])
def collaborative_recommendations(user_id):

    if svd_model is None:
        return jsonify({
            "error": "SVD model is not available"
        }), 503

    try:

        # Load saved SVD model components
        users = svd_model["users"]
        products = svd_model["products"]

        user_to_idx = svd_model["user_to_idx"]
        predicted_matrix = svd_model["predicted_matrix"]
        full_matrix = svd_model["full_matrix"]

        product_names = svd_model["product_names"]

        # Number of recommendations
        top_n = request.args.get(
            "limit",
            default=10,
            type=int
        )

        if not 1 <= top_n <= 50:
            return jsonify({
                "error": "Limit must be between 1 and 50"
            }), 400

        recommendations = []

        # ----------------------------------
        # EXISTING USER
        # ----------------------------------

        if user_id in user_to_idx:

            user_index = user_to_idx[user_id]

            # Identify previously interacted products
            seen_indices = np.where(
                full_matrix[user_index] > 0
            )[0]

            seen_products = {
                int(products[index])
                for index in seen_indices
            }

            # Sort products by predicted SVD score
            scores = predicted_matrix[user_index]

            ranked_indices = np.argsort(scores)[::-1]

            for index in ranked_indices:

                product_id = int(products[index])

                if product_id in seen_products:
                    continue

                recommendations.append({
                    "product_id": product_id,
                    "name": product_names.get(
                        product_id,
                        f"Product {product_id}"
                    ),
                    "recommendation_score": round(
                        float(scores[index]), 4
                    )
                })

                if len(recommendations) >= top_n:
                    break

            recommendation_type = "SVD Collaborative Filtering"

        # ----------------------------------
        # NEW USER: POPULARITY FALLBACK
        # ----------------------------------

        else:

            popularity = full_matrix.sum(axis=0)

            ranked_indices = np.argsort(
                popularity
            )[::-1]

            for index in ranked_indices:

                if popularity[index] <= 0:
                    continue

                product_id = int(products[index])

                recommendations.append({
                    "product_id": product_id,
                    "name": product_names.get(
                        product_id,
                        f"Product {product_id}"
                    ),
                    "recommendation_score": round(
                        float(popularity[index]), 4
                    )
                })

                if len(recommendations) >= top_n:
                    break

            recommendation_type = "Popularity-Based Fallback"

        return jsonify({
            "user_id": user_id,
            "algorithm": recommendation_type,
            "recommendations": recommendations
        }), 200

    except Exception as error:

        print("SVD recommendation error:", error)

        return jsonify({
            "error": "Unable to generate collaborative recommendations"
        }), 500


# ==========================================
# RUN SERVER
# ==========================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True
    )
