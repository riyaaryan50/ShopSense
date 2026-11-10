
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import text

from app.extensions import db, jwt


def create_app():
    app = Flask(__name__)

    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)

    database_url = os.getenv("DATABASE_URL")
    jwt_secret = os.getenv("JWT_SECRET_KEY")

    if not database_url:
        raise RuntimeError("DATABASE_URL missing from .env")

    if not jwt_secret:
        raise RuntimeError("JWT_SECRET_KEY missing from .env")

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = jwt_secret
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600

    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    @app.route("/", methods=["GET"])
    def home():
        return jsonify({
            "message": "Welcome to ShopSense AI Backend!",
            "status": "Running successfully"
        })

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "healthy",
            "project": "ShopSense AI"
        })

    @app.route("/api/db-health", methods=["GET"])
    def database_health():
        try:
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))

            return jsonify({
                "database": "connected",
                "status": "healthy"
            }), 200

        except Exception:
            app.logger.exception("Database connection failed")
            return jsonify({
                "database": "disconnected",
                "status": "error"
            }), 500

    # Register authentication routes
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    from app.routes.product import product_bp
    app.register_blueprint(product_bp)

    return app
