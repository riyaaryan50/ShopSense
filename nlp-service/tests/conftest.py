import json
import os
import sys
from pathlib import Path

import pytest

SERVICE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SERVICE_DIR))
os.environ.setdefault("FORCE_TFIDF_EMBEDDINGS", "1")

from common.services import NLPServices  # noqa: E402
from search.semantic_search import SemanticSearchIndex, TfidfEmbedder  # noqa: E402

CATALOG = SERVICE_DIR.parent / "backend" / "product_catalog.json"
CATALOG_SIZE = len(json.loads(CATALOG.read_text(encoding="utf-8")))
KETTLES = {13, 44}  # Philips and Prestige electric kettles

REVIEWS = {
    7: [  # Sony headphones – mostly positive
        (5, "Absolutely love it! Battery life is amazing and the sound quality is clear."),
        (5, "Excellent purchase. Sound quality is crisp, battery life lasts for days."),
        (4, "Very good overall. Comfortable and the battery life is great."),
        (2, "Disappointing. The microphone quality is poor on calls."),
        (4, "Good value. Sound quality is great for lectures."),
    ],
    8: [  # boAt headphones – mixed / negative build
        (1, "Terrible, do not buy. Build quality is cheap plastic and the headband cracked."),
        (2, "Not satisfied. The plastic hinge broke, build quality is poor."),
        (5, "Superb product. Bass is punchy and battery lasts long."),
        (1, "Worst purchase ever. Build quality is awful and it broke in a week."),
    ],
    20: [  # printer – negative about ink
        (1, "Very bad experience. Ink cartridges are expensive and run out quickly."),
        (2, "Disappointing. Ink cost is very high and printing is slow."),
        (4, "Good value for money. Print quality is sharp for assignments."),
    ],
}


class FakeDataSource:
    """Offline stand-in for the backend: catalogue JSON + in-memory reviews."""

    last_source = "fake"

    def __init__(self):
        products = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.products = [dict(p, price=float(p["price"])) for p in products]
        self.reviews = {
            pid: [{"id": i + 1 + pid * 100, "product_id": pid, "rating": r,
                   "comment": c, "created_at": None}
                  for i, (r, c) in enumerate(items)]
            for pid, items in REVIEWS.items()
        }

    def get_products(self, force=False):
        return self.products

    def get_reviews(self, product_id, force=False):
        return self.reviews.get(int(product_id), [])

    def get_all_reviews(self):
        return [r for items in self.reviews.values() for r in items]

    def invalidate_reviews(self, product_id=None):
        pass


@pytest.fixture(scope="session")
def services(tmp_path_factory):
    index = SemanticSearchIndex(embedder=TfidfEmbedder(),
                                artifact_dir=tmp_path_factory.mktemp("artifacts"))
    svc = NLPServices(datasource=FakeDataSource(), index=index)
    svc.sync()
    return svc
