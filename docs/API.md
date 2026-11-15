# ShopSense AI – API reference

All endpoints return JSON. Endpoints marked **JWT** need `Authorization: Bearer <access_token>`
from `POST /api/auth/login`. Base URLs (local): backend `http://127.0.0.1:5000`,
recommendation service `:5001`, NLP service `:5002`. The frontend only talks to the backend,
which proxies the AI services.

## Backend (Flask, port 5000)

### Auth
| Method | Path | Auth | Body / params | Returns |
|---|---|---|---|---|
| POST | `/api/auth/register` | – | `{name, email, password}` (password ≥ 8 chars) | `{message, user_id}` · 409 if email exists |
| POST | `/api/auth/login` | – | `{email, password}` | `{access_token, refresh_token, user}` |
| POST | `/api/auth/refresh` | refresh JWT | – | `{access_token}` |
| GET | `/api/auth/profile` | JWT | – | `{id, name, email}` |

### Products
| Method | Path | Auth | Body / params | Returns |
|---|---|---|---|---|
| GET | `/api/products/` | – | `category`, `q`, `sort` (`price_asc`, `price_desc`, `name`, `newest`), `page`, `limit` | array of products, `X-Total-Count` header |
| GET | `/api/products/<id>` | – | – | product |
| GET | `/api/products/search` | – | `q` | `{query, total, results}` (keyword fallback) |
| GET | `/api/products/categories` | – | – | `[{name, count}]` |
| POST / PUT / DELETE | `/api/products/` · `/api/products/<id>` | JWT | product fields | product |

### Cart, wishlist, interactions, reviews
| Method | Path | Auth | Body | Notes |
|---|---|---|---|---|
| GET / POST | `/api/cart/` | JWT | `{product_id, quantity}` | `GET` returns `{items, total_items, total_quantity, total_price}` |
| PUT / DELETE | `/api/cart/<cart_item_id>` | JWT | `{quantity}` | |
| GET / POST | `/api/wishlist/` | JWT | `{product_id}` | 409 if already in wishlist |
| DELETE | `/api/wishlist/<wishlist_item_id>` | JWT | – | |
| GET / POST | `/api/interactions/` | JWT | `{product_id, event_type}` | events: `view, click, wishlist, cart, purchase` |
| GET | `/api/interactions/product/<id>` | JWT | – | |
| POST | `/api/reviews/` | JWT | `{product_id, rating 1-5, comment}` | one review per user per product; refreshes the NLP summary |
| GET | `/api/reviews/product/<id>` | – | – | `{total_reviews, reviews}` |
| GET | `/api/reviews/my-reviews` | JWT | – | |

### Survey
| Method | Path | Auth | Body | Returns |
|---|---|---|---|---|
| POST | `/api/survey/` | JWT | `{answers}` | saved survey |
| GET | `/api/survey/` | JWT | – | latest answers · 404 if none |
| POST | `/api/survey/recommendations` | optional JWT | `{answers?, top_k?}` (guests must send `answers`) | `{engine, recommendations: [product + match_score + reasons]}` |

`answers` keys: `role` (`school, undergrad, postgrad, professional, other`), `interests` (category
names), `uses` (`online_classes, coding, note_taking, music, hostel_living, travel, printing,
exam_prep, entertainment, photography`), `budget_min`, `budget_max`, `priorities` (`price,
performance, battery, portability, durability, comfort, display, brand`), `brands`, `description`.

### AI gateway
| Method | Path | Auth | Returns |
|---|---|---|---|
| POST | `/api/search/semantic` | – | `{query, engine, latency_ms, results: [product + score]}`; keyword fallback if NLP is down |
| GET | `/api/reviews/<id>/summary` | – | sentiment summary (see NLP service) |
| GET | `/api/similar/<id>?limit=5` | – | `{source, recommendations}` (content-based → embeddings → same category) |
| GET | `/api/recommendations/popular?limit=10` | – | popularity baseline |
| GET | `/api/recommendations/me?limit=10` | JWT | blended hybrid + content + survey + popularity, with `reason`, `sources_used`, `explanation`, `cached` |
| GET | `/api/recommendations/<user_id>` | JWT (same user) | same as `/me` |

Recommendations are cached under `user:{id}:recs` for 1 hour (Redis if `REDIS_URL` is set,
otherwise in memory) and invalidated on cart, wishlist, interaction and survey changes.

## Recommendation service (Flask, port 5001)
| Method | Path | Returns |
|---|---|---|
| GET | `/api/recommendations/<product_id>` | TF-IDF similar products |
| GET | `/api/personalized/<user_id>` (Bearer token) | content-based recommendations with fuzzy weights |
| GET | `/api/collaborative/<user_id>` | NumPy SVD recommendations / popularity fallback |
| GET | `/collab/recommend/<user_id>?limit=10` | Surprise SVD recommendations / popularity fallback |
| GET | `/collab/predict/<user_id>/<product_id>` | Surprise SVD predicted rating |

Member 3's hybrid FastAPI service (`recommendation_model/hybrid_api.py`): `GET /recommend/{user_id}?top_k=10`,
`GET /similar/{product_id}?top_k=10`.

## NLP service (Flask + Socket.IO, port 5002)
See [`nlp-service/README.md`](../nlp-service/README.md): `/api/nlp/search`, `/api/nlp/similar/<id>`,
`/api/nlp/sentiment`, `/api/nlp/reviews/<id>/summary`, `/api/nlp/survey/recommend`, `/api/nlp/chat`,
Socket.IO namespace `/chat` (`message` → `response`).
