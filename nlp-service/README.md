# ShopSense NLP Service (Member 4)

Semantic search, review sentiment, review summaries, survey matching and the
shopping-assistant chatbot. It's a Flask and Flask-SocketIO app on port **5002**.

```
nlp-service/
├── app.py                 Flask + Socket.IO app (REST + /chat namespace)
├── wsgi.py                gunicorn entry point (Docker)
├── config.py              env-configurable settings
├── common/
│   ├── text_cleaning.py   clean_text (embeddings/themes) vs light_clean (VADER)
│   ├── datasource.py      products + reviews from the backend, CSV fallback
│   └── services.py        wires index, analyzer, classifier, summary cache
├── search/semantic_search.py   MiniLM-L6-v2 embeddings -> FAISS IndexFlatIP
├── sentiment/analyzer.py       VADER (+ small e-commerce lexicon)
├── sentiment/summary.py        counts, TF-IDF themes, verdict
├── chatbot/intents.py          rule-based intent router + entity extraction
├── chatbot/handlers.py         one handler per intent -> structured JSON
├── survey/recommender.py       survey answers -> semantic + rule scoring
├── benchmarks/benchmark.py     latency, relevance, sentiment, intent accuracy
└── tests/                      91 unit/integration tests (incl. Socket.IO)
```

## Run locally

```bash
# from the repo root, with the backend running on :5000 (it supplies products & reviews)
python -m venv .venv && .venv/Scripts/activate          # source .venv/bin/activate on macOS/Linux
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r nlp-service/requirements.txt
cd nlp-service && python app.py                         # http://127.0.0.1:5002/health
```

The first start downloads `all-MiniLM-L6-v2` (~90 MB) and writes the FAISS
index to `artifacts/`. Later starts reuse it, and the index is rebuilt
automatically when the product catalogue changes. If the model can't be loaded
(offline), the service falls back to TF-IDF vectors and `/health` reports
`embedding_engine: tfidf-fallback`. If the backend is down, products and
reviews are read from `data/` (written by `backend/scripts/seed_demo_data.py`).

## API

| Method | Path | Purpose |
|---|---|---|
| GET  | `/health` | engine, index size, data source |
| POST | `/api/nlp/search` | `{query, top_k, category?, min_price?, max_price?}` → product IDs + cosine scores + latency |
| GET  | `/api/nlp/similar/<id>?top_k=5` | embedding nearest neighbours |
| POST | `/api/nlp/sentiment` | `{text}` or `{texts: [...]}` → compound + label |
| GET  | `/api/nlp/reviews/<id>/summary?include_reviews=true` | `{positive_count, negative_count, neutral_count, overall_sentiment, top_positive_themes, top_negative_themes, verdict, ...}` |
| POST | `/api/nlp/survey/recommend` | `{answers, top_k, exclude_ids}` → ranked products with match % and reasons |
| POST | `/api/nlp/chat` | REST fallback for the chatbot (`session_id` keeps context) |
| POST | `/api/nlp/reindex` | rebuild index, clear caches |
| WS   | Socket.IO namespace `/chat` | client emits `message {text, token?, user_name?}`; server emits `response` |

The backend proxies these as `/api/search/semantic`, `/api/reviews/<id>/summary`
and `/api/survey/recommendations`. When a new review is posted, the backend
calls `/api/nlp/reviews/<id>/invalidate` so the summary updates immediately.

### Chat response shape

```json
{ "intent": "compare_products", "confidence": 0.9, "type": "comparison",
  "text": "Here's a side-by-side comparison:",
  "products": [], "comparison": {"products": [...], "rows": [{"label": "Price", "values": ["₹11,099", "₹26,999"]}], "verdict": "..."},
  "summary": null, "suggestions": ["What do people say about ...?"], "entities": {...} }
```

`type` is one of `text | products | comparison | review_summary | product_info`.

## Chatbot intents

| Intent | Example | Handler |
|---|---|---|
| greeting | "hi", "thanks" | welcome + suggestions |
| help | "what can you do?" | capability list |
| search_product (default) | "something to keep my tea hot under 2000" | FAISS search, budget filter, category boost |
| get_recommendation | "recommend something for me" / "suggest headphones" | backend `/api/recommendations/me` (history + survey + popularity), or search re-ranked by review sentiment |
| compare_products | "compare Galaxy Tab A9 vs Tab S9 FE", "compare them" | price/brand/rating/sentiment/themes/specs table + verdict |
| review_summary | "what do people say about it?" | sentiment summary |
| product_info | "tell me about the Casio calculator" | specs, price, review stats |
| fallback | "???" | suggestions |

Entity extraction covers product names (weighted by how identifying each token
is, so model numbers like `ch520` or `a9` decide), budgets ("under 5k",
"between 2000 and 4000"), categories ("earbuds" → Audio), and pronouns. "it",
"them" and "both" resolve to the products in the previous answer.

## Tests and benchmarks

```bash
cd nlp-service
python -m pytest -q                               # 91 tests, ~2 s (TF-IDF embedder, fake data)
python -m benchmarks.benchmark --distilbert       # needs backend or data/ exports
```

Results go to `reports/benchmark_results.md`. Latest run (MiniLM, CPU):

* Search latency p95 **15–21 ms** across runs (target < 200 ms)
* Natural-language relevance: the expected product was in the top 3 for **15/15** queries
* Intent accuracy: **30/30** labelled queries
* Sentiment on 100 reviews vs star ratings: VADER 85%, VADER + domain lexicon 82%, DistilBERT-SST2 56%. On all 240 reviews, VADER and VADER + domain tie at 81%, and the domain lexicon fixes product-level verdicts such as the printer's "ink cartridges are expensive".

> **Data caveat:** the review corpus is **synthetic demo data** generated by
> `backend/scripts/review_bank.py`, because the repo has no real reviews for this
> catalogue. The sentiment numbers show the pipeline works. They aren't a claim
> about real-world accuracy, so re-run the benchmark when real reviews exist.
