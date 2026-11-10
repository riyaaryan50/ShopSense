
from app import create_app
from app.extensions import db
from app import models

# Create Flask application
app = create_app()

# Create tables in PostgreSQL
with app.app_context():
    db.create_all()

    print("ShopSense database tables created successfully!")

    print("Tables:", list(db.metadata.tables.keys()))
