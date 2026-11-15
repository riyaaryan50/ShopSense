# ShopSense AI

A student-focused e-commerce platform that uses machine learning, deep learning and NLP to help students
find the right products: a first laptop, an exam calculator, hostel essentials.

- **Hybrid recommendations:** content-based (TF-IDF with fuzzy interaction weights), SVD collaborative
  filtering, Neural Collaborative Filtering (NeuMF), survey-based matching and a popularity baseline,
  blended into one ranked list that explains each suggestion.
- **Preference survey:** new users get personalised picks on their first visit (cold start).
- **Semantic search:** "something to keep my tea hot in class" finds the thermos (MiniLM + FAISS).
- **Review intelligence:** VADER sentiment per review, praise and complaint themes, and a verdict.
- **Shopping assistant:** a real-time chatbot that searches, recommends, compares products and
  summarises reviews.

## Team

| Member | Area |
|---|---|
| Aanchal Yadav | React frontend, content-based recommender |
| Riya Aryan | Flask backend and database, SVD collaborative filtering, fuzzy weights |
| Susmita | Neural Collaborative Filtering (PyTorch), hybrid engine (FastAPI) |
| Sneha | NLP service (semantic search, sentiment, chatbot), preference survey, integration and deployment |

## Repository layout

```
frontend/              React + Vite + Tailwind single-page app
backend/               Flask REST API, AI gateway, survey, seed data (scripts/), Alembic migrations
recommendation_model/  content-based, SVD (NumPy + Surprise), NCF, hybrid, model comparison
nlp-service/           semantic search, sentiment, review summaries, chatbot, survey matching
api/index.py           single-function Vercel deployment (lite mode)
data/                  shared dataset exports (products, synthetic reviews, interactions)
docs/                  API reference and demo screenshots
report/                project report (LaTeX source + PDF)
docker-compose.yml     full stack: Postgres, Redis, backend, recommender, NLP, frontend
```

## Run it

**Docker (full stack):**

```bash
docker compose up --build
# frontend http://localhost:5173 · backend :5000 · recommender :5001 · NLP :5002
```

**Without Docker:**

```bash
python -m venv .venv && .venv/Scripts/activate              # source .venv/bin/activate on macOS/Linux
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r backend/requirements.txt -r recommendation_model/requirements.txt -r nlp-service/requirements.txt

cp backend/.env.example backend/.env                        # SQLite by default
cd backend && python -m scripts.seed_demo_data && python run.py      # :5000
cd recommendation_model && python recommendation_api.py              # :5001
cd nlp-service && python app.py                                      # :5002
cd frontend && npm install && npm run dev                            # :5173
```

Demo logins (password `ShopSense@123`): `demo.coder@shopsense.ai`, `demo.hostel@shopsense.ai`,
`demo.music@shopsense.ai`, and `demo.new@shopsense.ai` (new user, no history).

**Vercel:** import the repository in Vercel and set `DATABASE_URL` (Postgres, e.g. Neon) and
`JWT_SECRET_KEY`. `vercel.json` builds the frontend and runs the API as one Python function in lite
mode (TF-IDF search vectors, REST chat). The database is seeded on first use.

## Tests and evaluation

```bash
cd backend && python -m pytest tests -q                    # 15 tests
cd nlp-service && python -m pytest -q                      # 91 tests
cd nlp-service && python -m benchmarks.benchmark           # search latency, relevance, sentiment, intents
python -m recommendation_model.evaluate_models             # Popularity vs SVD vs CB vs NCF vs Hybrid
python -m recommendation_model.surprise_svd                # train + evaluate Surprise SVD
```

Results: [`nlp-service/reports/benchmark_results.md`](nlp-service/reports/benchmark_results.md) and
[`recommendation_model/reports/model_comparison.md`](recommendation_model/reports/model_comparison.md).

> The review corpus is **synthetic demo data** (`backend/scripts/review_bank.py`), because no real
> reviews existed for this catalogue. Treat the sentiment and model numbers as evidence that the pipeline
> works, not as real-world accuracy.

## Documentation

- [API reference](docs/API.md)
- [NLP service](nlp-service/README.md)
- [Demo walkthrough with screenshots](docs/demo/README.md)
- [Project report (PDF)](report/ShopSense_AI_Report.pdf) · [LaTeX source](report/shopsense_report.tex)
