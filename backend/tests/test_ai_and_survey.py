"""Tests for the survey API, AI gateway routes, product filters and token refresh.

The AI microservices are replaced with fakes, so these run without the NLP or
recommendation services. Run from backend/:  python -m pytest -q
"""

import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-hs256"

from app import create_app  # noqa: E402
from app import ai_clients  # noqa: E402
from app import cache  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Interaction, Product, Review, User  # noqa: E402
from app.routes import ai as ai_routes  # noqa: E402
from app.routes import survey as survey_routes  # noqa: E402

PRODUCTS = [
    (1, "Sony WH-CH520 Headphones", "Audio", "Sony", 4490),
    (2, "boAt Rockerz 430", "Audio", "boAt", 1499),
    (3, "Philips Electric Kettle", "Hostel Essentials", "Philips", 1795),
    (4, "HP 15s Laptop", "Laptops", "HP", 52990),
]


def service_down(*_args, **_kwargs):
    raise ai_clients.ServiceUnavailable("down")


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setattr(ai_routes, "call", service_down)
    monkeypatch.setattr(survey_routes, "call", service_down)
    monkeypatch.setattr(ai_clients, "call", service_down)
    # Fresh databases reuse user IDs, so start every test with an empty cache.
    monkeypatch.setattr(cache, "_backend", cache._MemoryCache())
    application = create_app()
    application.testing = True
    with application.app_context():
        db.create_all()
        for pid, name, category, brand, price in PRODUCTS:
            db.session.add(Product(id=pid, name=name, category=category, brand=brand,
                                   price=price, stock=10, description=f"{name} description"))
        reviewer = User(name="R", email="r@x.io", password_hash="x")
        db.session.add(reviewer)
        db.session.flush()
        db.session.add(Review(user_id=reviewer.id, product_id=3, rating=5, comment="great"))
        for _ in range(3):
            db.session.add(Interaction(user_id=reviewer.id, product_id=2, event_type="purchase"))
        db.session.commit()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email="user@x.io"):
    client.post("/api/auth/register", json={"name": "U", "email": email,
                                            "password": "password123"})
    data = client.post("/api/auth/login", json={"email": email,
                                                "password": "password123"}).get_json()
    return data


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------- #
def test_login_returns_refresh_token_that_refreshes(client):
    data = login(client)
    assert data["refresh_token"]
    refreshed = client.post("/api/auth/refresh", headers=auth(data["refresh_token"]))
    assert refreshed.status_code == 200
    assert refreshed.get_json()["access_token"]
    # An access token cannot be used to refresh.
    assert client.post("/api/auth/refresh",
                       headers=auth(data["access_token"])).status_code == 422


def test_product_filters_sort_and_pagination(client):
    audio = client.get("/api/products/?category=Audio&sort=price_asc").get_json()
    assert [p["id"] for p in audio] == [2, 1]
    page = client.get("/api/products/?limit=2&page=2")
    assert [p["id"] for p in page.get_json()] == [3, 4]
    assert page.headers["X-Total-Count"] == "4"
    assert client.get("/api/products/search?q=kettle").get_json()["results"][0]["id"] == 3
    cats = client.get("/api/products/categories").get_json()
    assert {"name": "Audio", "count": 2} in cats


def test_survey_save_get_and_validation(client):
    token = login(client)["access_token"]
    assert client.get("/api/survey/", headers=auth(token)).status_code == 404
    bad = client.post("/api/survey/", headers=auth(token), json={"answers": {"role": "x"}})
    assert bad.status_code == 400
    ok = client.post("/api/survey/", headers=auth(token), json={"answers": {
        "role": "undergrad", "interests": ["Audio"], "budget_max": 3000,
        "unknown_key": "dropped"}})
    assert ok.status_code == 201
    saved = client.get("/api/survey/", headers=auth(token)).get_json()["answers"]
    assert saved == {"role": "undergrad", "interests": ["Audio"], "budget_max": 3000.0}


def test_survey_recommendations_fallback_when_nlp_down(client):
    response = client.post("/api/survey/recommendations", json={
        "answers": {"interests": ["Audio"], "budget_max": 3000}})
    data = response.get_json()
    assert response.status_code == 200
    assert data["engine"] == "rule-based-fallback"
    assert data["recommendations"][0]["id"] == 2  # Audio AND within budget
    assert "Within your ₹3,000 budget" in data["recommendations"][0]["reasons"]


def test_survey_recommendations_use_nlp_service(client, monkeypatch):
    def fake_call(method, base, path, **kwargs):
        assert path == "/api/nlp/survey/recommend"
        return 200, {"engine": "minilm", "recommendations": [
            {"product_id": 1, "match_score": 91.0, "reasons": ["Closely matches"]}]}
    monkeypatch.setattr(survey_routes, "call", fake_call)
    data = client.post("/api/survey/recommendations",
                       json={"answers": {"interests": ["Audio"]}}).get_json()
    assert data["engine"] == "minilm"
    assert data["recommendations"][0]["name"].startswith("Sony")
    assert data["recommendations"][0]["match_score"] == 91.0


def test_guest_needs_answers_for_survey_recommendations(client):
    assert client.post("/api/survey/recommendations", json={}).status_code == 400


def test_popular_baseline(client):
    data = client.get("/api/recommendations/popular?limit=2").get_json()
    assert [p["id"] for p in data["recommendations"]] == [2, 3]


def test_cold_start_user_gets_popular_with_survey_prompt(client):
    token = login(client)["access_token"]
    data = client.get("/api/recommendations/me", headers=auth(token)).get_json()
    assert data["cold_start"] is True
    assert data["sources_used"] == ["popular"]
    assert "survey" in data["explanation"]


def test_survey_personalises_blended_recommendations(client):
    token = login(client)["access_token"]
    client.post("/api/survey/", headers=auth(token), json={"answers": {
        "interests": ["Laptops"], "budget_max": 60000}})
    data = client.get("/api/recommendations/me", headers=auth(token)).get_json()
    assert "survey" in data["sources_used"]
    assert data["cold_start"] is False
    assert data["recommendations"][0]["id"] == 4
    assert data["recommendations"][0]["reason"].startswith("Matches your interest")


def test_recommendations_for_other_user_forbidden(client):
    token = login(client)["access_token"]
    assert client.get("/api/recommendations/9999", headers=auth(token)).status_code == 403


def test_semantic_search_falls_back_to_keywords(client):
    data = client.post("/api/search/semantic", json={"query": "kettle"}).get_json()
    assert data["engine"] == "keyword-fallback"
    assert data["results"][0]["id"] == 3


def test_semantic_search_enriches_nlp_results(client, monkeypatch):
    monkeypatch.setattr(ai_routes, "call", lambda *a, **k: (200, {
        "engine": "minilm", "latency_ms": 12, "product_ids": [3, 1], "scores": [0.6, 0.2]}))
    data = client.post("/api/search/semantic", json={"query": "boil water"}).get_json()
    assert [(r["id"], r["score"]) for r in data["results"]] == [(3, 0.6), (1, 0.2)]


def test_review_summary_proxy_503_when_down(client):
    assert client.get("/api/reviews/1/summary").status_code == 503
    assert client.get("/api/reviews/999/summary").status_code == 404


def test_similar_products_category_fallback(client):
    data = client.get("/api/similar/1").get_json()
    assert data["source"] == "same-category fallback"
    assert [p["id"] for p in data["recommendations"]] == [2]


def test_recommendations_cached_and_invalidated_on_change(client):
    token = login(client)["access_token"]
    first = client.get("/api/recommendations/me", headers=auth(token)).get_json()
    second = client.get("/api/recommendations/me", headers=auth(token)).get_json()
    assert first["cached"] is False and second["cached"] is True
    assert second["recommendations"] == first["recommendations"]
    # Taking the survey must invalidate the cached list.
    client.post("/api/survey/", headers=auth(token), json={"answers": {"interests": ["Laptops"]}})
    third = client.get("/api/recommendations/me", headers=auth(token)).get_json()
    assert third["cached"] is False
    assert "survey" in third["sources_used"]


def test_cached_recommendations_show_fresh_product_details(client, app):
    token = login(client)["access_token"]
    first = client.get("/api/recommendations/me", headers=auth(token)).get_json()
    pid = first["recommendations"][0]["id"]
    with app.app_context():
        db.session.get(Product, pid).image_url = "/images/new.jpg"
        db.session.commit()
    second = client.get("/api/recommendations/me", headers=auth(token)).get_json()
    assert second["cached"] is True
    assert second["recommendations"][0]["image_url"] == "/images/new.jpg"
