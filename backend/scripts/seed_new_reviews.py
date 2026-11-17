import random
from app import create_app
from app.extensions import db
from app.models import Product, Review
from scripts.seed_demo_data import get_or_create_user

rng = random.Random(42)

aspects = {
    "Laptops": ["performance", "battery life", "display", "keyboard"],
    "Tablets": ["display", "battery life", "multitasking", "portability"],
    "Smartphones": ["camera", "battery life", "display", "performance"],
    "Audio": ["sound quality", "comfort", "clarity", "build quality"],
    "Computer Accessories": ["build quality", "connectivity", "ease of use", "design"],
    "Study Essentials": ["quality", "usability", "design", "value for money"],
    "Hostel Essentials": ["performance", "build quality", "ease of use", "design"],
    "Backpacks": ["storage capacity", "comfort", "stitching", "design"],
    "Storage & Data": ["transfer speed", "build quality", "portability", "connectivity"],
}

positive = [
    "The {} is excellent.",
    "Really impressed with the {}.",
    "Very happy with the {}.",
    "The {} exceeded my expectations.",
    "Good {} for everyday student use.",
]

negative = [
    "The {} could be better.",
    "Disappointed with the {}.",
    "The {} did not meet my expectations.",
    "Not very satisfied with the {}.",
    "The {} needs improvement.",
]

app = create_app()

with app.app_context():
    products = Product.query.filter(
        Product.id.between(2, 51)
    ).order_by(Product.id).all()

    if len(products) != 50:
        raise RuntimeError("Expected 50 products.")

    reviewers = [
        get_or_create_user(
            f"Demo Reviewer {i:02d}",
            f"reviewer{i:02d}@shopsense.demo"
        )
        for i in range(1, 17)
    ]

    created = 0

    for product in products:
        count = Review.query.filter_by(
            product_id=product.id
        ).count()

        ratings = [5, 5, 5, 5, 4, 4, 4, 3, 3, 2, 2, 1]
        rng.shuffle(ratings)

        features = aspects.get(
            product.category,
            ["quality", "design", "usability"]
        )

        for reviewer in rng.sample(reviewers, len(reviewers)):
            if count >= 12:
                break

            if Review.query.filter_by(
                product_id=product.id,
                user_id=reviewer.id
            ).first():
                continue

            rating = ratings[count]
            a, b = rng.sample(features, 2)

            good = rng.choice(positive).format(a)
            bad = rng.choice(negative).format(b)

            if rating == 5:
                comment = good + " Highly recommended for students."
            elif rating == 4:
                comment = good + " " + bad
            elif rating == 3:
                comment = "Average experience. " + good + " " + bad
            elif rating == 2:
                comment = bad + " Expected better for the price."
            else:
                comment = bad + " Would not recommend this product."

            db.session.add(Review(
                user_id=reviewer.id,
                product_id=product.id,
                rating=rating,
                comment="[Synthetic demo review] " + comment
            ))

            count += 1
            created += 1

        print(f"{product.name}: {count} reviews")

    db.session.commit()

    print("New reviews added:", created)
    print("Total reviews:", Review.query.count())
