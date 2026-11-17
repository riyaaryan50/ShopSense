"""Vercel serverless entry point: the whole ShopSense API in one function.

Vercel cannot run several long-lived services, so the backend (Member 2), the
content-based/SVD recommender (Members 1 & 2) and the NLP service (Member 4)
are loaded into one process and call each other in-process instead of over
HTTP. Routing:

    /api/nlp/*   -> NLP service (search, sentiment, survey matching, chat)
    /api/*       -> Flask backend (auth, products, cart, reviews, AI gateway)

Lite-mode differences from the Docker deployment:
  * semantic search uses TF-IDF vectors (PyTorch/MiniLM exceed Vercel's size limit)
  * the chatbot uses REST (POST /api/nlp/chat) because WebSockets are not supported
"""

import importlib.util
import logging
import os
import secrets
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
# Order matters: the backend's `app` package must win over nlp-service/app.py
# (the NLP app module is loaded explicitly by file path below).
for folder in ("recommendation_model", "nlp-service", "backend"):
    sys.path.insert(0, str(ROOT / folder))

# ---- environment for lite mode ------------------------------------------
os.environ.setdefault("FORCE_TFIDF_EMBEDDINGS", "1")
os.environ.setdefault("ARTIFACT_DIR", "/tmp/shopsense-artifacts")
os.environ.setdefault("DATA_DIR", str(ROOT / "data"))
os.environ["NLP_SERVICE_URL"] = "inproc://nlp"
os.environ["CB_SERVICE_URL"] = "inproc://cb"
os.environ["BACKEND_URL"] = "http://inproc"
os.environ["BACKEND_API_URL"] = "http://inproc/api"
if not os.getenv("DATABASE_URL"):
    # Demo fallback: SQLite in /tmp, re-seeded on every cold start.
    os.environ["DATABASE_URL"] = "sqlite:////tmp/shopsense.db"
if not os.getenv("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = secrets.token_hex(32)
db_url = os.environ["DATABASE_URL"]
if db_url.startswith("postgres://"):
    db_url = "postgresql://" + db_url[len("postgres://"):]
if db_url.startswith("postgresql://"):
    os.environ["DATABASE_URL"] = "postgresql+psycopg://" + db_url[len("postgresql://"):]

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("shopsense-vercel")

# ---- 1. Backend ------------------------------------------------------------
from app import create_app  # noqa: E402  (backend package)
from app import ai_clients  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Product  # noqa: E402

backend_app = create_app()


def seed_if_empty():
    """Create tables and load demo data the first time the database is used."""
    seeded = False
    with backend_app.app_context():
        db.create_all()
        if Product.query.count():
            return
        import random

        from scripts import seed_demo_data as seed
        os.environ["DATA_DIR"] = "/tmp/shopsense-data"
        rng = random.Random(42)
        catalog = seed.upsert_products()
        seed.seed_demo_users(rng)
        seed.seed_reviews(rng, catalog)
        log.info("Seeded demo database")
        seeded = True
    if seeded:
        # Riya's script: synthetic reviews for the products added in the
        # 50-product catalogue (idempotent; skips products with 12 reviews).
        import runpy
        runpy.run_module("scripts.seed_new_reviews", run_name="__main__")
        log.info("Seeded reviews for the expanded catalogue")


seed_if_empty()


class InprocessResponse:
    def __init__(self, response):
        self._response = response
        self.status_code = response.status_code

    def json(self):
        return self._response.get_json(silent=True)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"in-process request failed: {self.status_code}")


class InprocessHTTP:
    """Minimal `requests`-compatible client that calls the backend in-process."""

    def get(self, url, headers=None, params=None, timeout=None):
        path = urlsplit(url).path
        query = urlsplit(url).query
        response = backend_app.test_client().get(
            path + (f"?{query}" if query else ""), headers=headers, query_string=params)
        return InprocessResponse(response)


inprocess_http = InprocessHTTP()

# ---- 2. Content-based + SVD recommender (Members 1 & 2) -------------------
import recommender  # noqa: E402

recommender.requests = inprocess_http  # product + interaction fetches stay in-process
import recommendation_api  # noqa: E402

ai_clients.INPROCESS_APPS["cb"] = recommendation_api.app

# ---- 3. NLP service (Member 4) --------------------------------------------
from common.datasource import DataSource  # noqa: E402
from common.services import NLPServices  # noqa: E402

nlp_services = NLPServices(datasource=DataSource(session=inprocess_http))
nlp_services.http = inprocess_http  # chatbot -> /api/recommendations/me

spec = importlib.util.spec_from_file_location("nlp_app", ROOT / "nlp-service" / "app.py")
nlp_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nlp_module)
nlp_app = nlp_module.create_app(services=nlp_services)

ai_clients.INPROCESS_APPS["nlp"] = nlp_app


# ---- 4. Router ---------------------------------------------------------------
def app(environ, start_response):
    path = environ.get("PATH_INFO", "")
    if path.startswith("/api/nlp/") or path == "/api/nlp":
        return nlp_app(environ, start_response)
    return backend_app(environ, start_response)
