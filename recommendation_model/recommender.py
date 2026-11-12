
import requests
import pandas as pd
import numpy as np
from fuzzy_weights import calculate_adaptive_event_weights
from collections import defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ==========================================
# API CONFIGURATION
# ==========================================

API_BASE = "http://127.0.0.1:5000/api"

PRODUCT_API = f"{API_BASE}/products/"
INTERACTION_API = f"{API_BASE}/interactions/"
CART_API = f"{API_BASE}/cart/"


# ==========================================
# INTERACTION WEIGHTS
# ==========================================

EVENT_WEIGHTS = {
    "view": 1.0,
    "click": 1.5,
    "wishlist": 2.5,
    "cart": 3.0,
    "purchase": 5.0,
}

# ==========================================
# SEMANTIC PRODUCT KEYWORDS
# ==========================================

PRODUCT_KEYWORDS = {

    2: (
        "audio music sound listening wireless bluetooth "
        "headset headphones earphones noise cancellation "
        "portable audio device consumer electronics"
    ),

    3: (
        "computer accessories pc gaming typing keyboard "
        "mechanical switches rgb gaming equipment "
        "computer input device"
    ),

    4: (
        "computer accessories laptop pc wireless bluetooth "
        "pointing device mouse ergonomic dpi "
        "computer input device"
    ),

    5: (
        "clothing apparel casual wear cotton everyday "
        "fashion t shirt garments"
    ),

    6: (
        "lighting home decor study desk lamp led "
        "illumination brightness home furnishing"
    ),

    7: (
        "kitchen cookware cooking utensils frying pan "
        "nonstick kitchen equipment food preparation"
    ),

    8: (
        "kitchen appliance blender mixer grinder "
        "food preparation blending grinding smoothie "
        "home appliance"
    ),

    9: (
        "books fiction novel inspirational dreams "
        "personal journey storytelling self discovery "
        "reading literature"
    ),

    10: (
        "cricket sports equipment batting outdoor game "
        "cricket bat sports training"
    ),

    11: (
        "kitchen appliance water heating beverage "
        "electric kettle stainless steel home appliance "
        "hot water"
    ),

    12: (
        "fashion bags backpack travel storage "
        "compartments luggage everyday accessories"
    ),

    13: (
        "consumer electronics mobile smartphone android "
        "portable device touchscreen camera communication "
        "digital technology bluetooth"
    ),

    14: (
        "books self improvement self help habits "
        "personal development productivity nonfiction "
        "reading motivation"
    ),

    15: (
        "books personal finance money management "
        "investing business financial education "
        "wealth management nonfiction"
    ),

    16: (
        "sports fitness exercise yoga stretching "
        "workout fitness equipment flexibility "
        "physical training"
    ),

    17: (
        "clothing fashion apparel denim jeans "
        "casual wear trousers pants garments"
    ),

    18: (
        "sports football soccer ball outdoor game "
        "sports equipment team training"
    ),

    19: (
        "sports fitness strength training workout "
        "weights dumbbells home gym exercise "
        "muscle building fitness equipment"
    ),

    20: (
        "consumer electronics wearable technology "
        "smartwatch fitness tracker health monitoring "
        "heart rate activity tracking bluetooth "
        "portable digital device"
    ),

    21: (
        "fashion footwear running shoes sports shoes "
        "athletic footwear jogging running exercise "
        "cushioned sole"
    )
}


class ProductRecommender:

    def __init__(self):

        self.products = None
        self.tfidf_matrix = None
        self.similarity_matrix = None
        self.vectorizer = None

    # ==========================================
    # LOAD PRODUCTS
    # ==========================================

    def load_products(self):
        """Fetch products from Flask backend."""

        try:

            response = requests.get(
                PRODUCT_API,
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            if isinstance(data, dict):
                data = data.get("products", [])

            if not data:
                raise ValueError("No products found.")

            self.products = pd.DataFrame(data)

            for column in [
                "id",
                "name",
                "description",
                "category"
            ]:

                if column not in self.products.columns:
                    self.products[column] = ""

            self.products = (
                self.products
                .fillna("")
                .reset_index(drop=True)
            )

            self.products["id"] = (
                self.products["id"].astype(int)
            )

            print(
                f"Successfully loaded {len(self.products)} products."
            )

            return True

        except Exception as error:

            print("Error loading products:", error)

            return False

    # ==========================================
    # BUILD TF-IDF MODEL
    # ==========================================


    def build_model(self):
        """Build an enhanced semantic TF-IDF product model."""

        if self.products is None or self.products.empty:
           print("Please load products first.")
           return False

        # Add semantic keywords to every product
        self.products["semantic_keywords"] = (
            self.products["id"]
            .map(PRODUCT_KEYWORDS)
            .fillna("")
        )

        # Combine all product information
        self.products["features"] = (
            self.products["name"].astype(str) + " " +
            self.products["name"].astype(str) + " " +
            self.products["description"].astype(str) + " " +
            self.products["category"].astype(str) + " " +
            self.products["semantic_keywords"].astype(str)
        )

        # Build enhanced TF-IDF vectors
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True
        )

        self.tfidf_matrix = self.vectorizer.fit_transform(
            self.products["features"]
        )

        # Calculate product-to-product similarity
        self.similarity_matrix = cosine_similarity(
            self.tfidf_matrix
        )

        print("Enhanced TF-IDF model built successfully.")
        print("Semantic keywords incorporated.")
        print("Cosine similarity matrix created.")

        return True


    # ==========================================
    # SIMILAR PRODUCTS
    # ==========================================

    def recommend(self, product_id, top_n=5):
        """Find products similar to a particular product."""

        if self.similarity_matrix is None:
            return []

        matching_indices = self.products.index[
            self.products["id"] == int(product_id)
        ].tolist()

        if not matching_indices:
            return []

        product_index = matching_indices[0]

        scores = list(enumerate(
            self.similarity_matrix[product_index]
        ))

        scores = [
            item for item in scores
            if item[0] != product_index
        ]

        scores.sort(
            key=lambda item: item[1],
            reverse=True
        )

        recommended_indices = [
            index for index, score in scores[:top_n]
        ]

        return self.products.iloc[
            recommended_indices
        ].drop(
            columns=["features"],
            errors="ignore"
        ).to_dict(orient="records")

    # ==========================================
    # FETCH USER INTERACTIONS
    # ==========================================

    def get_user_interactions(self, user_id, token):
        """Fetch interaction history of a particular user."""

        try:

            response = requests.get(
                INTERACTION_API,
                headers={
                    "Authorization": f"Bearer {token}"
                },
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            if isinstance(data, dict):
                interactions = data.get("interactions", [])
            else:
                interactions = data

            return [
                item for item in interactions
                if item.get("user_id") is None
                or str(item.get("user_id")) == str(user_id)
            ]

        except Exception as error:

            print("Error fetching interactions:", error)

            return []

    # ==========================================
    # FETCH ACTIVE CART PRODUCTS
    # ==========================================

    def get_active_cart_product_ids(self, token):
        """Get products currently present in the user's cart."""

        active_cart_products = set()

        try:

            response = requests.get(
                CART_API,
                headers={
                    "Authorization": f"Bearer {token}"
                },
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            if isinstance(data, list):
                items = data
            else:
                items = data.get("items", [])

            for item in items:

                product_id = item.get("product_id")

                if product_id is not None:
                    active_cart_products.add(int(product_id))

        except Exception as error:

            print(
                "Warning: Could not fetch active cart:",
                error
            )

        return active_cart_products

    # ==========================================
    # PERSONALIZED RECOMMENDATIONS
    # ==========================================

    def recommend_for_user(
    self,
    user_id,
    token,
    top_n=5,
    weight_mode="fuzzy"
    ):
        """
        Generate personalized recommendations using:

        1. User interaction history
        2. Repeated interaction weights
        3. TF-IDF user preference profile
        4. Item-to-item similarity
        5. Category diversity
        6. Cart and purchase exclusion
        """

        if self.tfidf_matrix is None:

            print("Build the model first.")

            return []

        if top_n <= 0:
            return []

        # ======================================
        # FETCH USER INTERACTION HISTORY
        # ======================================

        interactions = self.get_user_interactions(
            user_id,
            token
        )

        if not interactions:

            print("No interaction history available.")

            return []

        # ======================================
        # GROUP INTERACTIONS BY PRODUCT
        # ======================================

        grouped = defaultdict(
            lambda: defaultdict(int)
        )

        for interaction in interactions:

            product_id = interaction.get("product_id")

            event_type = interaction.get("event_type")

            if (
                product_id is None
                or event_type not in EVENT_WEIGHTS
            ):
                continue

            try:

                product_id = int(product_id)

            except (ValueError, TypeError):

                continue

            grouped[product_id][event_type] += 1

        if not grouped:
            return []

        # ======================================
        # SELECT INTERACTION WEIGHTING MODE
        # ======================================

        if weight_mode == "fuzzy":

            event_weights = calculate_adaptive_event_weights(
                interactions
            )

        elif weight_mode == "fixed":

            event_weights = EVENT_WEIGHTS.copy()

        else:

            raise ValueError(
                "Invalid weight mode. Use 'fixed' or 'fuzzy'."
            )

        print(
            f"{weight_mode.upper()} weights for user {user_id}:",
            event_weights
        )

        # ======================================
        # BUILD PRODUCT ID INDEX
        # ======================================

        product_index_map = {
            int(product_id): index
            for index, product_id in enumerate(
                self.products["id"]
            )
        }

        weighted_vectors = []

        total_weight = 0.0

        purchased_products = set()

        interaction_weight_vector = np.zeros(
            len(self.products),
            dtype=float
        )

        # ======================================
        # CALCULATE INTERACTION WEIGHTS
        # ======================================

        for product_id, event_counts in grouped.items():

            product_index = product_index_map.get(
                product_id
            )

            if product_index is None:
                continue

            product_weight = 0.0

            # Previously purchased products
            # will not be recommended again.

            if event_counts.get("purchase", 0) > 0:

                purchased_products.add(product_id)

            for event_type, count in event_counts.items():

                base_weight = event_weights[event_type]

                # Repeated interactions receive
                # diminishing additional influence.

                multiplier = min(
                    1.0 + 0.20 * (count - 1),
                    3.0
                )

                product_weight += (
                    base_weight * multiplier
                )

            if product_weight <= 0:
                continue

            # Add weighted product vector
            weighted_vectors.append(
                self.tfidf_matrix[product_index]
                * product_weight
            )

            interaction_weight_vector[product_index] = (
                product_weight
            )

            total_weight += product_weight

        if not weighted_vectors or total_weight == 0:

            return []

        # ======================================
        # CREATE USER PREFERENCE PROFILE
        # ======================================

        user_profile = weighted_vectors[0].copy()

        for vector in weighted_vectors[1:]:

            user_profile = user_profile + vector

        user_profile = user_profile / total_weight

        # ======================================
        # CONTENT-BASED SIMILARITY
        # ======================================

        profile_scores = cosine_similarity(
            user_profile,
            self.tfidf_matrix
        ).flatten()

        # ======================================
        # ITEM-TO-ITEM SIMILARITY
        # ======================================

        item_similarity_scores = (
            self.similarity_matrix.T.dot(
                interaction_weight_vector
            ) / total_weight
        )

        item_similarity_scores = np.asarray(
            item_similarity_scores
        ).flatten()

        # ======================================
        # COMBINE RECOMMENDATION SCORES
        # ======================================

        # 65% user preference profile
        # 35% similarity to interacted products

        final_scores = (
            0.65 * profile_scores +
            0.35 * item_similarity_scores
        )

        # ======================================
        # EXCLUDE ACTIVE CART AND PURCHASED ITEMS
        # ======================================

        active_cart_products = (
            self.get_active_cart_product_ids(token)
        )

        excluded_products = (
            purchased_products | active_cart_products
        )

        # Wishlist products are NOT excluded.
        # Their wishlist interactions influence scores.

        candidate_indices = [

            index

            for index, product_id in enumerate(
                self.products["id"]
            )

            if int(product_id) not in excluded_products
        ]

        if not candidate_indices:

            print("No eligible products available.")

            return []

        # ======================================
        # SORT PRODUCTS BY PERSONALIZED SCORE
        # ======================================

        remaining = sorted(
            candidate_indices,
            key=lambda index: final_scores[index],
            reverse=True
        )

        # ======================================
        # CATEGORY DIVERSITY
        # ======================================

        recommendations = []

        category_counts = {}

        max_per_category = 3

        while (
            remaining
            and len(recommendations) < top_n
        ):

            # Prefer categories with fewer
            # already selected products.

            eligible = [

                index

                for index in remaining

                if category_counts.get(
                    str(
                        self.products.iloc[index]["category"]
                    ),
                    0
                ) < max_per_category
            ]

            # Relax category restriction if
            # additional recommendations are needed.

            if not eligible:

                eligible = remaining

            best_index = max(
                eligible,
                key=lambda index: final_scores[index]
            )

            remaining.remove(best_index)

            product = self.products.iloc[
                best_index
            ].drop(
                labels=["features"],
                errors="ignore"
            ).to_dict()

            category = str(
                product.get("category", "General")
            )

            category_counts[category] = (
                category_counts.get(category, 0) + 1
            )

            product["recommendation_score"] = round(
                float(final_scores[best_index]),
                4
            )

            recommendations.append(product)

        # ======================================
        # PRINT RECOMMENDATION SUMMARY
        # ======================================

        print("\nPersonalized Recommendation Summary")
        print("----------------------------------")

        print("User ID:", user_id)

        print(
            "Unique interacted products:",
            len(grouped)
        )

        print(
            "Purchased products:",
            len(purchased_products)
        )

        print(
            "Currently in cart:",
            len(active_cart_products)
        )

        print(
            "Excluded products:",
            len(excluded_products)
        )

        print(
            "Eligible products:",
            len(candidate_indices)
        )

        print(
            "Recommendations generated:",
            len(recommendations)
        )

        print("\nRecommended Products:")

        for product in recommendations:

            print(
                product["name"],
                "|",
                product["category"],
                "| Score:",
                product["recommendation_score"]
            )

        return recommendations


# ==========================================
# TEST RECOMMENDATION MODEL
# ==========================================

if __name__ == "__main__":

    recommender = ProductRecommender()

    if recommender.load_products():

        if recommender.build_model():

            results = recommender.recommend(
                product_id=7,
                top_n=5
            )

            print("\nSimilar Products:\n")

            for product in results:

                print(product["name"])
