"""Semantic product search: sentence-transformers embeddings + FAISS.

Pipeline (Day 1 / Day 2 of the plan):
    product -> name + brand + category + description + specs -> clean_text
            -> all-MiniLM-L6-v2 (384-dim) -> L2 normalise
            -> faiss.IndexFlatIP  (inner product on unit vectors == cosine)

The index is saved to ``artifacts/`` together with a fingerprint of the
catalogue, so it is only rebuilt when products change.
"""

import hashlib
import json
import logging
import threading
import time

import faiss
import numpy as np

import config
from common.text_cleaning import clean_text, product_text

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------- #
# Embedding back-ends
# ---------------------------------------------------------------------- #
class TransformerEmbedder:
    """all-MiniLM-L6-v2 sentence embeddings (384 dimensions)."""

    def __init__(self, model_name):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name, device="cpu")
        self.name = model_name
        self._lock = threading.Lock()

    def fit(self, texts):  # transformer is pre-trained; nothing to fit
        return self

    def encode(self, texts):
        with self._lock:
            vectors = self.model.encode(
                list(texts),
                batch_size=32,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        return np.ascontiguousarray(vectors, dtype="float32")


class TfidfEmbedder:
    """Offline fallback so the service still works without the HF model."""

    name = "tfidf-fallback"

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 2), sublinear_tf=True
        )

    def fit(self, texts):
        self.vectorizer.fit(list(texts))
        return self

    def encode(self, texts):
        matrix = self.vectorizer.transform(list(texts)).toarray().astype("float32")
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return np.ascontiguousarray(matrix / norms, dtype="float32")


def load_embedder(model_name=None, force_tfidf=None):
    force_tfidf = config.FORCE_TFIDF_EMBEDDINGS if force_tfidf is None else force_tfidf
    if not force_tfidf:
        try:
            return TransformerEmbedder(model_name or config.EMBEDDING_MODEL)
        except Exception as error:  # noqa: BLE001
            log.warning("Could not load sentence-transformer (%s). "
                        "Falling back to TF-IDF embeddings.", error)
    return TfidfEmbedder()


# ---------------------------------------------------------------------- #
# FAISS index
# ---------------------------------------------------------------------- #
class SemanticSearchIndex:
    def __init__(self, embedder=None, artifact_dir=None):
        self.embedder = embedder or load_embedder()
        self.artifact_dir = artifact_dir or config.ARTIFACT_DIR
        self.index = None
        self.product_ids = []
        self.products = {}
        self.vectors = None
        self.fingerprint = None
        self.built_at = None
        self._lock = threading.RLock()

    @property
    def engine(self):
        return self.embedder.name

    @property
    def size(self):
        return 0 if self.index is None else self.index.ntotal

    # -------------------------------------------------------------- #
    def build(self, products, use_cache=True):
        """(Re)build the index for ``products``. Returns True if rebuilt."""
        products = sorted(products, key=lambda p: int(p["id"]))
        texts = [product_text(p) for p in products]
        fingerprint = hashlib.sha1(
            (self.engine + "\n" + "\n".join(texts)).encode("utf-8")
        ).hexdigest()

        with self._lock:
            if fingerprint == self.fingerprint:
                return False

            self.embedder.fit(texts)
            vectors = None
            if use_cache and isinstance(self.embedder, TransformerEmbedder):
                vectors = self._load_cached(fingerprint, len(texts))
            rebuilt = vectors is None
            if vectors is None:
                vectors = self.embedder.encode(texts)

            index = faiss.IndexFlatIP(vectors.shape[1])
            index.add(vectors)

            self.index = index
            self.vectors = vectors
            self.product_ids = [int(p["id"]) for p in products]
            self.products = {int(p["id"]): p for p in products}
            self.fingerprint = fingerprint
            self.built_at = time.time()

            if rebuilt and isinstance(self.embedder, TransformerEmbedder):
                self._save(fingerprint)

        log.info("FAISS index ready: %d products, dim=%d, engine=%s, %s",
                 self.size, vectors.shape[1], self.engine,
                 "rebuilt" if rebuilt else "loaded from disk")
        return True

    def _paths(self):
        return (self.artifact_dir / "products.faiss",
                self.artifact_dir / "index_meta.json")

    def _save(self, fingerprint):
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        index_path, meta_path = self._paths()
        faiss.write_index(self.index, str(index_path))
        meta_path.write_text(json.dumps({
            "fingerprint": fingerprint,
            "engine": self.engine,
            "product_ids": self.product_ids,
            "dimension": int(self.vectors.shape[1]),
            "built_at": self.built_at,
        }, indent=2))

    def _load_cached(self, fingerprint, expected):
        index_path, meta_path = self._paths()
        if not (index_path.exists() and meta_path.exists()):
            return None
        try:
            meta = json.loads(meta_path.read_text())
            if meta.get("fingerprint") != fingerprint:
                return None
            index = faiss.read_index(str(index_path))
            if index.ntotal != expected:
                return None
            return index.reconstruct_n(0, index.ntotal).astype("float32")
        except Exception as error:  # noqa: BLE001
            log.warning("Ignoring unreadable FAISS cache: %s", error)
            return None

    # -------------------------------------------------------------- #
    def encode_query(self, text):
        return self.embedder.encode([clean_text(text)])

    def search(self, query, top_k=10, category=None, min_price=None,
               max_price=None, min_score=None, exclude_ids=None):
        """Return ``[{"product_id", "score"}]`` ordered by cosine similarity.

        Filters are applied after retrieval. The catalogue is small, so we
        retrieve every product; for a large catalogue fetch ``top_k * 5``.
        """
        if not query or not query.strip() or self.size == 0:
            return []

        with self._lock:
            vector = self.encode_query(query)
            scores, indices = self.index.search(vector, self.size)
            ids = list(self.product_ids)
            products = self.products

        exclude_ids = set(exclude_ids or [])
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            pid = ids[idx]
            product = products[pid]
            if pid in exclude_ids:
                continue
            if category and (product.get("category") or "").lower() != category.lower():
                continue
            if min_price is not None and product["price"] < min_price:
                continue
            if max_price is not None and product["price"] > max_price:
                continue
            if min_score is not None and score < min_score:
                continue
            results.append({"product_id": pid, "score": round(float(score), 4)})
            if len(results) >= top_k:
                break
        return results

    def similar(self, product_id, top_k=5):
        product_id = int(product_id)
        with self._lock:
            if product_id not in self.products:
                return None
            row = self.product_ids.index(product_id)
            vector = self.vectors[row:row + 1]
            scores, indices = self.index.search(vector, self.size)
            ids = list(self.product_ids)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            pid = ids[idx]
            if pid == product_id:
                continue
            results.append({"product_id": pid, "score": round(float(score), 4)})
            if len(results) >= top_k:
                break
        return results

    def similarity_to_all(self, text):
        """Cosine similarity of free text to every product: {product_id: score}."""
        if not text or not text.strip() or self.size == 0:
            return {}
        with self._lock:
            vector = self.encode_query(text)
            sims = (self.vectors @ vector[0]).tolist()
            ids = list(self.product_ids)
        return dict(zip(ids, sims))
