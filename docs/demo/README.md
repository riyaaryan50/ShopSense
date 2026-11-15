# ShopSense demo walkthrough (feat/nlp-chatbot)

Captured with Playwright (headless Edge) against the running stack:
backend :5000 (SQLite + seeded demo data), recommendation API :5001, NLP service :5002, Vite :5173.

| # | Screenshot | What it shows |
|---|---|---|
| 1 | `01_home_guest_survey_cta_trending.png` | Guest home: survey call-to-action + "Trending Now" (popularity baseline) |
| 2 | `02_semantic_search.png` | "something to keep my tea hot in class" → thermos, kettle (MiniLM + FAISS, relevance %) |
| 3 | `03a/03b/03c_survey_*.png` | 5-step preference survey → ranked matches with % and reasons |
| 4 | `04_home_logged_in_recommendations.png` | demo.coder: blended recs (browsing history + survey + popularity) with reasons |
| 5 | `05_product_review_analysis.png` | HP printer: VADER sentiment bar, themes, AI verdict, per-review labels, review form |
| 5b | `05b_similar_products.png` | Similar products (content-based TF-IDF via gateway) |
| 6 | `06a–06d_chat_*.png` | Floating chat over WebSocket: search with budget, comparison table, review summary, personal recs |
| 7 | `07_mobile_chat_followup.png` | Mobile width: "tell me about the Sony WH-CH520" → "what do people think about it?" (pronoun resolved) |

Demo logins (password `ShopSense@123`): `demo.coder@shopsense.ai`, `demo.hostel@shopsense.ai`,
`demo.music@shopsense.ai`, `demo.new@shopsense.ai` (cold start).

Some product photos are hosted by third-party retailers that block hot-linking, so a few cards show a placeholder.
