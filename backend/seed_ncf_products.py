
import csv
from pathlib import Path

from sqlalchemy import text

from app import create_app
from app.extensions import db
from app import models


ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "product_id_mapping.csv"

# Read the original NCF product catalogue
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    products = list(csv.DictReader(f))

if len(products) != 20:
    raise RuntimeError("Expected 20 NCF products")

ids = [int(p["product_id"]) for p in products]

if len(set(ids)) != len(ids):
    raise RuntimeError("Duplicate product IDs found")

app = create_app()

with app.app_context():

    # Safety check: only change the new development database
    db_name = db.session.execute(
        text("SELECT current_database()")
    ).scalar_one()

    if db_name != "shopsense_ncf_dev":
        raise RuntimeError(
            f"Wrong database: {db_name}. "
            "Expected shopsense_ncf_dev."
        )

    count = db.session.execute(
        text("SELECT COUNT(*) FROM products")
    ).scalar_one()

    if count != 0:
        raise RuntimeError(
            "Products table is not empty. "
            "Import stopped to prevent conflicts."
        )

    try:
        for product in products:
            db.session.execute(
                text("""
                    INSERT INTO products
                    (id, name, description, category,
                     price, stock, image_url)
                    VALUES
                    (:id, :name, :description, :category,
                     :price, :stock, :image_url)
                """),
                {
                    "id": int(product["product_id"]),
                    "name": product["product_name"],
                    "description": product["product_name"],
                    "category": "Uncategorized",
                    "price": 0,
                    "stock": 0,
                    "image_url": None
                }
            )

        # Keep future automatically assigned IDs safe
        db.session.execute(text("""
            SELECT setval(
                pg_get_serial_sequence('products', 'id'),
                (SELECT MAX(id) FROM products),
                true
            )
        """))

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    print("Original NCF products imported successfully!")
    print("Products imported:", len(products))
    print("Database:", db_name)
    print("Product IDs:", sorted(ids))
