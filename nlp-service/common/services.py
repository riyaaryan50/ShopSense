"""Wires the NLP components together and keeps them in sync with the catalogue."""

import logging
import threading
import time

import requests

import config
from chatbot.intents import IntentClassifier
from common.datasource import DataSource
from search.semantic_search import SemanticSearchIndex
from sentiment.analyzer import SentimentAnalyzer
from sentiment.summary import summarize_reviews

log = logging.getLogger(__name__)


def product_card(product, **extra):
    """Compact product representation used in API and chat responses."""
    card = {
        "id": product["id"],
        "name": product["name"],
        "brand": product.get("brand") or "",
        "category": product.get("category") or "",
        "price": product["price"],
        "original_price": product.get("original_price"),
        "image_url": product.get("image_url") or "",
        "description": product.get("description") or "",
    }
    card.update({k: v for k, v in extra.items() if v is not None})
    return card


class NLPServices:
    def __init__(self, datasource=None, index=None, analyzer=None):
        self.data = datasource or DataSource()
        self.index = index or SemanticSearchIndex()
        self.analyzer = analyzer or SentimentAnalyzer()
        self.classifier = None
        self._summary_cache = {}
        self._sync_lock = threading.Lock()
        self.http = requests.Session()

    # -------------------------------------------------------------- #
    def sync(self, force=False):
        """Refresh products; rebuild FAISS + matcher if the catalogue changed."""
        with self._sync_lock:
            products = self.data.get_products(force=force)
            rebuilt = self.index.build(products)
            if rebuilt or self.classifier is None:
                self.classifier = IntentClassifier(products)
            return rebuilt

    def products(self):
        self.sync()
        return self.index.products

    def product(self, product_id):
        return self.products().get(int(product_id))

    # -------------------------------------------------------------- #
    def review_summary(self, product_id, include_reviews=False, force=False):
        product_id = int(product_id)
        cached = self._summary_cache.get(product_id)
        if (cached and not force and not include_reviews
                and time.time() - cached[0] < config.CACHE_TTL_SECONDS):
            return cached[1]

        product = self.product(product_id)
        if product is None:
            return None
        reviews = self.data.get_reviews(product_id, force=force)
        summary = summarize_reviews(product, reviews, self.analyzer,
                                    include_reviews=include_reviews)
        if not include_reviews:
            self._summary_cache[product_id] = (time.time(), summary)
        return summary

    def positive_ratio(self, product_id):
        """Share of positive reviews (0-1), or None when there are no reviews."""
        summary = self.review_summary(product_id)
        if not summary or not summary["total_reviews"]:
            return None
        return summary["positive_count"] / summary["total_reviews"]

    def invalidate(self, product_id=None):
        self.data.invalidate_reviews(product_id)
        if product_id is None:
            self._summary_cache.clear()
        else:
            self._summary_cache.pop(int(product_id), None)

    # -------------------------------------------------------------- #
    def backend_get(self, path, token=None, params=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = self.http.get(f"{config.BACKEND_URL}{path}", headers=headers,
                                 params=params, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
