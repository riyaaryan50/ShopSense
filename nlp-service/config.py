"""Central configuration for the ShopSense NLP microservice (Member 4).

Every value can be overridden with an environment variable so the same code
runs locally, in Docker Compose and in tests.
"""

import os
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parent
REPO_ROOT = SERVICE_DIR.parent

# Where the Flask backend (Member 2) is running. Products and reviews are
# fetched from here so the NLP service always sees live data.
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5000").rstrip("/")

# Shared dataset exports (written by backend/scripts/seed_demo_data.py).
# Used as an offline fallback when the backend is not reachable.
DATA_DIR = Path(os.getenv("DATA_DIR", REPO_ROOT / "data"))
FALLBACK_CATALOG = REPO_ROOT / "backend" / "product_catalog.json"

# Saved FAISS index + metadata.
ARTIFACT_DIR = Path(os.getenv("ARTIFACT_DIR", SERVICE_DIR / "artifacts"))

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

# Set to "1" to skip loading the transformer (e.g. in unit tests or when the
# machine is offline). The service then falls back to TF-IDF vectors.
FORCE_TFIDF_EMBEDDINGS = os.getenv("FORCE_TFIDF_EMBEDDINGS", "0") == "1"

# VADER thresholds from the sprint plan.
POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05

# How long product / review data is cached in memory (seconds).
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "60"))

HOST = os.getenv("NLP_HOST", "127.0.0.1")
PORT = int(os.getenv("NLP_PORT", "5002"))

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "5"))
