"""Seed the database with demo data and export the shared dataset CSVs.

Creates / updates:
  * products      from backend/product_catalog.json (upsert by id)
  * demo users    with personas, interaction history and survey answers
  * reviewers     + SYNTHETIC reviews (see scripts/review_bank.py)
  * data/         products.json, products.csv, reviews.csv, interactions.csv
                  (shared exports for Members 1, 3 and 4)

Usage (from backend/):
    python -m scripts.seed_demo_data            # idempotent
    python -m scripts.seed_demo_data --reset    # drop & recreate all tables first

Demo logins (password for all: ShopSense@123):
    demo.coder@shopsense.ai     laptops / accessories persona + survey
    demo.hostel@shopsense.ai    hostel essentials persona + survey
    demo.music@shopsense.ai     audio persona + survey
    demo.new@shopsense.ai       brand-new user: no history, no survey (cold start)
"""

import argparse
import csv
import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import text
from werkzeug.security import generate_password_hash

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import (  # noqa: E402
    CartItem, Interaction, Product, Review, SurveyResponse, User, WishlistItem,
)
from scripts.review_bank import (  # noqa: E402
    ASPECTS, KNOWN_WEAKNESS, OPENERS, PRODUCT_KIND, RATING_WEIGHTS,
)

DEMO_PASSWORD = "ShopSense@123"
REVIEWS_PER_PRODUCT = 12
NUM_REVIEWERS = 16
NOW = datetime.now(timezone.utc)

DEMO_USERS = [
    {
        "name": "Demo Coder", "email": "demo.coder@shopsense.ai",
        "events": [(3, "view"), (3, "view"), (2, "view"), (3, "click"), (9, "view"),
                   (9, "cart"), (10, "view"), (10, "wishlist"), (19, "view")],
        "survey": {
            "role": "undergrad", "interests": ["Laptops", "Computer Accessories"],
            "uses": ["coding", "online_classes"], "budget_max": 65000,
            "priorities": ["performance", "battery"], "brands": ["Lenovo", "HP"],
            "description": "A reliable setup for programming assignments and online classes",
        },
    },
    {
        "name": "Demo Hosteller", "email": "demo.hostel@shopsense.ai",
        "events": [(13, "view"), (13, "wishlist"), (14, "view"), (14, "cart"),
                   (18, "view"), (12, "view"), (12, "click")],
        "survey": {
            "role": "undergrad", "interests": ["Hostel Essentials", "Backpacks"],
            "uses": ["hostel_living", "travel"], "budget_max": 3000,
            "priorities": ["price", "durability"],
            "description": "Moving into a hostel and need everyday essentials on a budget",
        },
    },
    {
        "name": "Demo Music Fan", "email": "demo.music@shopsense.ai",
        "events": [(7, "view"), (7, "view"), (8, "view"), (7, "wishlist"),
                   (6, "view"), (6, "click")],
        "survey": {
            "role": "undergrad", "interests": ["Audio", "Smartphones"],
            "uses": ["music", "entertainment", "online_classes"], "budget_max": 20000,
            "priorities": ["battery", "comfort"],
            "description": "Headphones with good battery for music and lectures",
        },
    },
    {"name": "Demo Newbie", "email": "demo.new@shopsense.ai", "events": [], "survey": None},
]


# ---------------------------------------------------------------------- #
def lower_first(sentence):
    return sentence[0].lower() + sentence[1:] if sentence else sentence


def compose_review(rng, product_id, rating):
    aspects = ASPECTS[PRODUCT_KIND[product_id]]
    names = list(aspects)
    rng.shuffle(names)
    weakness = KNOWN_WEAKNESS.get(product_id)

    def pos(aspect):
        return rng.choice(aspects[aspect][0])

    def neg(aspect):
        return rng.choice(aspects[aspect][1])

    def neg_aspect():
        if weakness and rng.random() < 0.7:
            return weakness
        return rng.choice(names)

    opener = rng.choice(OPENERS[rating])
    if rating == 5:
        body = [pos(names[0]), pos(names[1])]
    elif rating == 4:
        weak = neg_aspect()
        good = next(n for n in names if n != weak)
        body = [pos(good), "Only downside: " + lower_first(neg(weak))]
    elif rating == 3:
        weak = neg_aspect()
        good = next(n for n in names if n != weak)
        body = [pos(good), "But " + lower_first(neg(weak))]
    elif rating == 2:
        weak = neg_aspect()
        other = next(n for n in names if n != weak)
        body = [neg(weak), "At least " + lower_first(pos(other))]
    else:
        weak = neg_aspect()
        other = next(n for n in names if n != weak)
        body = [neg(weak), neg(other)]
    return " ".join([opener] + body)


def upsert_products():
    catalog = json.loads((BACKEND_DIR / "product_catalog.json").read_text(encoding="utf-8"))
    for item in catalog:
        product = db.session.get(Product, item["id"]) or Product(id=item["id"])
        for field in ("name", "description", "category", "price", "image_url", "brand",
                      "original_price", "marketplace", "product_url",
                      "specifications", "marketplace_links"):
            if field in item:
                setattr(product, field, item[field])
        product.stock = item.get("stock", 50)
        db.session.add(product)
    db.session.commit()

    if db.engine.dialect.name == "postgresql":
        db.session.execute(text(
            "SELECT setval(pg_get_serial_sequence('products','id'), "
            "(SELECT MAX(id) FROM products), true)"))
        db.session.commit()
    return catalog


def get_or_create_user(name, email):
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(name=name, email=email,
                    password_hash=generate_password_hash(DEMO_PASSWORD))
        db.session.add(user)
        db.session.flush()
    return user


def seed_demo_users(rng):
    for spec in DEMO_USERS:
        user = get_or_create_user(spec["name"], spec["email"])
        if Interaction.query.filter_by(user_id=user.id).count() == 0:
            for offset, (product_id, event) in enumerate(spec["events"]):
                db.session.add(Interaction(
                    user_id=user.id, product_id=product_id, event_type=event,
                    created_at=NOW - timedelta(hours=len(spec["events"]) - offset)))
                if event == "cart" and not CartItem.query.filter_by(
                        user_id=user.id, product_id=product_id).first():
                    db.session.add(CartItem(user_id=user.id, product_id=product_id,
                                            quantity=1))
                if event == "wishlist" and not WishlistItem.query.filter_by(
                        user_id=user.id, product_id=product_id).first():
                    db.session.add(WishlistItem(user_id=user.id, product_id=product_id))
        if spec["survey"] and not SurveyResponse.query.filter_by(user_id=user.id).first():
            db.session.add(SurveyResponse(user_id=user.id, answers=spec["survey"]))
    db.session.commit()


def seed_reviews(rng, catalog):
    reviewers = [
        get_or_create_user(f"Reviewer {i:02d}", f"reviewer{i:02d}@shopsense.demo")
        for i in range(1, NUM_REVIEWERS + 1)
    ]
    db.session.commit()

    created = 0
    for item in catalog:
        pid = item["id"]
        if pid not in PRODUCT_KIND:
            continue
        if Review.query.filter_by(product_id=pid).count() >= REVIEWS_PER_PRODUCT:
            continue
        for reviewer in rng.sample(reviewers, REVIEWS_PER_PRODUCT):
            if Review.query.filter_by(user_id=reviewer.id, product_id=pid).first():
                continue
            rating = rng.choices([1, 2, 3, 4, 5], weights=RATING_WEIGHTS[pid])[0]
            when = NOW - timedelta(days=rng.randint(1, 120), hours=rng.randint(0, 23))
            db.session.add(Review(user_id=reviewer.id, product_id=pid, rating=rating,
                                  comment=compose_review(rng, pid, rating), created_at=when))
            # A review implies the reviewer bought (and viewed) the product.
            db.session.add(Interaction(user_id=reviewer.id, product_id=pid,
                                       event_type="view", created_at=when - timedelta(days=3)))
            db.session.add(Interaction(user_id=reviewer.id, product_id=pid,
                                       event_type="purchase", created_at=when - timedelta(days=2)))
            created += 1
    db.session.commit()
    return created


def export_dataset():
    data_dir = Path(os.getenv("DATA_DIR", REPO_ROOT / "data"))
    data_dir.mkdir(exist_ok=True)

    products = Product.query.order_by(Product.id).all()
    from app.routes.product import product_to_dict
    product_dicts = [product_to_dict(p) for p in products]
    (data_dir / "products.json").write_text(
        json.dumps(product_dicts, indent=2, ensure_ascii=False), encoding="utf-8")

    with open(data_dir / "products.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "name", "brand", "category", "price", "description"])
        for p in product_dicts:
            writer.writerow([p["id"], p["name"], p["brand"], p["category"], p["price"],
                             p["description"]])

    with open(data_dir / "reviews.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "user_id", "product_id", "rating", "comment", "created_at",
                         "synthetic"])
        for r in Review.query.order_by(Review.id).all():
            writer.writerow([r.id, r.user_id, r.product_id, r.rating, r.comment,
                             r.created_at.isoformat() if r.created_at else "", 1])

    interactions = Interaction.query.order_by(Interaction.created_at, Interaction.id).all()
    rows = [[i.user_id, i.product_id, i.event_type,
             i.created_at.isoformat() if i.created_at else ""] for i in interactions]
    targets = [data_dir / "interactions.csv"]
    if (REPO_ROOT / "recommendation_model").is_dir():  # not present inside Docker
        targets.append(REPO_ROOT / "recommendation_model" / "interactions.csv")
    for path in targets:
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["user_id", "product_id", "event_type", "created_at"])
            writer.writerows(rows)
    return len(product_dicts), len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true",
                        help="drop and recreate all tables before seeding")
    args = parser.parse_args()

    rng = random.Random(42)
    app = create_app()
    with app.app_context():
        if args.reset:
            db.drop_all()
        db.create_all()

        catalog = upsert_products()
        seed_demo_users(rng)
        reviews = seed_reviews(rng, catalog)
        n_products, n_interactions = export_dataset()

        print(f"Products: {n_products} | new reviews: {reviews} | "
              f"total reviews: {Review.query.count()} | interactions: {n_interactions}")
        print(f"Demo logins (password '{DEMO_PASSWORD}'):")
        for spec in DEMO_USERS:
            print(f"  {spec['email']:<28} {spec['name']}")
        print("Exports written to data/ (reviews are SYNTHETIC demo data).")


if __name__ == "__main__":
    main()
