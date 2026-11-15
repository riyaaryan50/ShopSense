"""Access to products and reviews.

Primary source is the Flask backend (live database). If the backend is down
the service falls back to the CSV/JSON exports in ``data/`` so search and
review summaries still work during development and in tests.
"""

import csv
import json
import logging
import threading
import time

import requests

import config

log = logging.getLogger(__name__)


class DataSource:
    def __init__(self, backend_url=None, data_dir=None, ttl=None, session=None):
        self.backend_url = (backend_url or config.BACKEND_URL).rstrip("/")
        self.data_dir = data_dir or config.DATA_DIR
        self.ttl = config.CACHE_TTL_SECONDS if ttl is None else ttl
        self.http = session or requests.Session()
        self._lock = threading.Lock()
        self._products = None
        self._products_at = 0.0
        self._reviews_cache = {}
        self.last_source = None

    # ------------------------------------------------------------------ #
    # Products
    # ------------------------------------------------------------------ #
    def get_products(self, force=False):
        with self._lock:
            fresh = time.time() - self._products_at < self.ttl
            if self._products is not None and fresh and not force:
                return self._products

        products = self._fetch_products_from_backend()
        source = "backend"
        if products is None:
            products = self._load_products_from_files()
            source = "file"

        products = [self._normalise_product(p) for p in products]
        products.sort(key=lambda p: p["id"])

        with self._lock:
            self._products = products
            self._products_at = time.time()
            self.last_source = source
        return products

    def product_by_id(self, product_id):
        product_id = int(product_id)
        for product in self.get_products():
            if product["id"] == product_id:
                return product
        return None

    def _fetch_products_from_backend(self):
        try:
            response = self.http.get(
                f"{self.backend_url}/api/products/", timeout=config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                data = data.get("products", [])
            return data or None
        except Exception as error:  # noqa: BLE001 - any failure -> fallback
            log.warning("Backend products unavailable (%s); using files", error)
            return None

    def _load_products_from_files(self):
        json_export = self.data_dir / "products.json"
        for path in (json_export, config.FALLBACK_CATALOG):
            if path.exists():
                with open(path, encoding="utf-8") as handle:
                    data = json.load(handle)
                return data if isinstance(data, list) else data.get("products", [])
        raise RuntimeError("No product data available (backend down, no exports)")

    @staticmethod
    def _normalise_product(product):
        product = dict(product)
        product["id"] = int(product["id"])
        product["price"] = float(product.get("price") or 0)
        product.setdefault("brand", "")
        product.setdefault("category", "")
        product.setdefault("description", "")
        product.setdefault("specifications", {})
        product.setdefault("image_url", "")
        return product

    # ------------------------------------------------------------------ #
    # Reviews
    # ------------------------------------------------------------------ #
    def get_reviews(self, product_id, force=False):
        product_id = int(product_id)
        cached = self._reviews_cache.get(product_id)
        if cached and not force and time.time() - cached[0] < self.ttl:
            return cached[1]

        reviews = self._fetch_reviews_from_backend(product_id)
        if reviews is None:
            reviews = [
                r for r in self._load_reviews_from_file()
                if r["product_id"] == product_id
            ]

        self._reviews_cache[product_id] = (time.time(), reviews)
        return reviews

    def get_all_reviews(self):
        """All reviews across the catalogue (used by benchmarks)."""
        reviews = []
        for product in self.get_products():
            reviews.extend(self.get_reviews(product["id"]))
        return reviews

    def invalidate_reviews(self, product_id=None):
        if product_id is None:
            self._reviews_cache.clear()
        else:
            self._reviews_cache.pop(int(product_id), None)

    def _fetch_reviews_from_backend(self, product_id):
        try:
            response = self.http.get(
                f"{self.backend_url}/api/reviews/product/{product_id}",
                timeout=config.REQUEST_TIMEOUT,
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
            return [
                {
                    "id": r.get("id"),
                    "product_id": int(r.get("product_id", product_id)),
                    "rating": int(r["rating"]) if r.get("rating") is not None else None,
                    "comment": r.get("comment") or "",
                    "created_at": r.get("created_at"),
                }
                for r in data.get("reviews", [])
            ]
        except Exception as error:  # noqa: BLE001
            log.warning("Backend reviews unavailable (%s); using files", error)
            return None

    def _load_reviews_from_file(self):
        path = self.data_dir / "reviews.csv"
        if not path.exists():
            return []
        with open(path, newline="", encoding="utf-8") as handle:
            return [
                {
                    "id": int(row["id"]),
                    "product_id": int(row["product_id"]),
                    "rating": int(row["rating"]),
                    "comment": row.get("comment", ""),
                    "created_at": row.get("created_at"),
                }
                for row in csv.DictReader(handle)
            ]
