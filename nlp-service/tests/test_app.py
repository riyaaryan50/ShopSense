import pytest

import app as nlp_app
from tests.conftest import CATALOG_SIZE, KETTLES


@pytest.fixture(scope="module")
def application(services):
    flask_app = nlp_app.create_app(services=services)
    flask_app.testing = True
    return flask_app


@pytest.fixture()
def client(application):
    return application.test_client()


def test_health(client):
    data = client.get("/health").get_json()
    assert data["status"] == "healthy"
    assert data["indexed_products"] == CATALOG_SIZE


def test_search_requires_query(client):
    assert client.post("/api/nlp/search", json={}).status_code == 400


def test_search_returns_ids_scores_and_latency(client):
    data = client.post("/api/nlp/search", json={"query": "electric kettle", "top_k": 3}).get_json()
    assert data["product_ids"][0] in KETTLES
    assert len(data["scores"]) == len(data["results"]) == 3
    assert data["latency_ms"] >= 0


def test_similar_endpoint(client):
    assert client.get("/api/nlp/similar/7").status_code == 200
    assert client.get("/api/nlp/similar/9999").status_code == 404


def test_sentiment_endpoint_single_and_batch(client):
    single = client.post("/api/nlp/sentiment", json={"text": "I love it!"}).get_json()
    assert single["label"] == "positive"
    batch = client.post("/api/nlp/sentiment",
                        json={"texts": ["awful", "great"]}).get_json()["results"]
    assert [r["label"] for r in batch] == ["negative", "positive"]
    assert client.post("/api/nlp/sentiment", json={}).status_code == 400


def test_review_summary_endpoint(client):
    data = client.get("/api/nlp/reviews/7/summary?include_reviews=true").get_json()
    for key in ("positive_count", "negative_count", "overall_sentiment",
                "top_positive_themes", "top_negative_themes", "reviews"):
        assert key in data
    assert client.get("/api/nlp/reviews/9999/summary").status_code == 404


def test_survey_endpoint(client):
    response = client.post("/api/nlp/survey/recommend", json={
        "answers": {"interests": ["Audio"], "budget_max": 5000}, "top_k": 3})
    data = response.get_json()
    assert response.status_code == 200
    assert len(data["recommendations"]) == 3
    assert data["recommendations"][0]["product"]["category"] == "Audio"
    assert client.post("/api/nlp/survey/recommend", json={}).status_code == 400


def test_rest_chat_keeps_session_context(client):
    first = client.post("/api/nlp/chat", json={
        "message": "tell me about the Sony WH-CH520", "session_id": "s1"}).get_json()
    assert first["intent"] == "product_info"
    second = client.post("/api/nlp/chat", json={
        "message": "what do people say about it", "session_id": "s1"}).get_json()
    assert second["summary"]["product_id"] == 7


def test_socketio_chat_roundtrip(application):
    socket_client = nlp_app.socketio.test_client(application, namespace="/chat")
    assert socket_client.is_connected("/chat")

    greeting = socket_client.get_received("/chat")
    assert greeting[0]["name"] == "response"
    assert greeting[0]["args"][0]["intent"] == "greeting"

    socket_client.emit("message", {"text": "compare galaxy tab a9 vs tab s9 fe"},
                       namespace="/chat")
    received = [e for e in socket_client.get_received("/chat") if e["name"] == "response"]
    payload = received[-1]["args"][0]
    assert payload["intent"] == "compare_products"
    assert [p["id"] for p in payload["comparison"]["products"]] == [4, 5]
    socket_client.disconnect(namespace="/chat")
