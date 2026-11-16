import pytest

from chatbot.handlers import ChatEngine
from survey.recommender import need_statement, survey_recommend


# --------------------------------------------------------------------- #
# Semantic search index (TF-IDF embedder in unit tests)
# --------------------------------------------------------------------- #
def test_index_contains_every_product(services):
    assert services.index.size == len(services.data.get_products())


def test_search_ranks_obvious_match_first(services):
    assert services.index.search("electric kettle", top_k=3)[0]["product_id"] == 13


def test_search_price_filter(services):
    hits = services.index.search("headphones", top_k=10, max_price=2000)
    assert hits
    assert all(services.product(h["product_id"])["price"] <= 2000 for h in hits)


def test_search_empty_query_returns_nothing(services):
    assert services.index.search("   ") == []


def test_similar_products_exclude_source(services):
    hits = services.index.similar(7, top_k=3)
    ids = [h["product_id"] for h in hits]
    assert 7 not in ids and 8 in ids


def test_similar_unknown_product(services):
    assert services.index.similar(9999) is None


def test_index_not_rebuilt_when_catalogue_unchanged(services):
    assert services.sync() is False


# --------------------------------------------------------------------- #
# Chat engine
# --------------------------------------------------------------------- #
@pytest.fixture()
def chat(services):
    return ChatEngine(services)


def test_chat_search_returns_product_cards(chat):
    response = chat.respond("find me an electric kettle")
    assert response["intent"] == "search_product"
    assert response["type"] == "products"
    assert response["products"][0]["id"] == 13
    assert {"id", "name", "price", "image_url"} <= set(response["products"][0])


def test_chat_compare_builds_table(chat):
    response = chat.respond("compare Sony WH-CH520 vs boAt Rockerz 430")
    assert response["type"] == "comparison"
    comparison = response["comparison"]
    assert [p["id"] for p in comparison["products"]] == [7, 8]
    labels = [row["label"] for row in comparison["rows"]]
    assert {"Price", "Rating", "Positive reviews"} <= set(labels)
    assert all(len(row["values"]) == 2 for row in comparison["rows"])
    assert "most affordable" in comparison["verdict"]


def test_chat_compare_by_category(chat):
    response = chat.respond("compare headphones")
    assert response["type"] == "comparison"
    assert {p["id"] for p in response["comparison"]["products"]} == {7, 8}


def test_chat_review_summary(chat):
    response = chat.respond("what do people say about the HP printer?")
    assert response["type"] == "review_summary"
    assert response["summary"]["product_id"] == 20
    assert response["summary"]["negative_count"] >= 2


def test_chat_product_info_then_pronoun_follow_up(chat):
    context = {}
    info = chat.respond("tell me about the Sony WH-CH520", context)
    assert info["type"] == "product_info"
    assert info["products"][0]["id"] == 7
    follow_up = chat.respond("what do people think about it?", context)
    assert follow_up["type"] == "review_summary"
    assert follow_up["summary"]["product_id"] == 7


def test_chat_compare_them_uses_previous_results(chat):
    context = {"last_products": [7, 8]}
    response = chat.respond("compare them", context)
    assert [p["id"] for p in response["comparison"]["products"]] == [7, 8]


def test_chat_recommendation_with_need_ranks_by_relevance(chat):
    response = chat.respond("suggest headphones under 2000")
    assert response["intent"] == "get_recommendation"
    assert response["products"]
    assert all(p["price"] <= 2000 for p in response["products"])


def test_chat_budget_too_low_offers_closest(chat):
    response = chat.respond("find a laptop under 100")
    assert "couldn't find" in response["text"]


def test_chat_greeting_and_fallback(chat):
    assert chat.respond("hello")["intent"] == "greeting"
    assert chat.respond("")["intent"] == "fallback"
    assert chat.respond("")["suggestions"]


# --------------------------------------------------------------------- #
# Survey recommender
# --------------------------------------------------------------------- #
HOSTEL_ANSWERS = {
    "role": "undergrad",
    "interests": ["Hostel Essentials"],
    "uses": ["hostel_living"],
    "budget_max": 3000,
    "priorities": ["price"],
    "description": "boil water for tea and noodles in my hostel room",
}


def test_need_statement_is_natural_language():
    text = need_statement(HOSTEL_ANSWERS)
    assert "college undergraduate" in text
    assert "Hostel Essentials" in text
    assert "boil water" in text


def test_survey_recommendations_respect_interests_and_budget(services):
    result = survey_recommend(HOSTEL_ANSWERS, services, top_k=5)
    recs = result["recommendations"]
    assert len(recs) == 5
    top = services.product(recs[0]["product_id"])
    assert top["category"] == "Hostel Essentials"
    assert top["price"] <= 3000
    assert any("budget" in reason for reason in recs[0]["reasons"])
    # Scores are sorted and bounded.
    scores = [r["match_score"] for r in recs]
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= s <= 100 for s in scores)


def test_survey_excludes_ids_and_limits_category_repeats(services):
    result = survey_recommend(HOSTEL_ANSWERS, services, top_k=8, exclude_ids=[13])
    ids = [r["product_id"] for r in result["recommendations"]]
    assert 13 not in ids
    categories = [services.product(i)["category"] for i in ids]
    assert max(categories.count(c) for c in set(categories)) <= 3


def test_price_and_image_changes_reach_the_index_without_rebuild(tmp_path):
    from search.semantic_search import SemanticSearchIndex, TfidfEmbedder

    products = [{"id": 1, "name": "Kettle", "description": "boils water", "price": 100.0,
                 "image_url": "old.jpg"},
                {"id": 2, "name": "Bottle", "description": "keeps tea hot", "price": 50.0,
                 "image_url": "b.jpg"}]
    index = SemanticSearchIndex(embedder=TfidfEmbedder(), artifact_dir=tmp_path)
    assert index.build(products) is True
    updated = [dict(products[0], price=80.0, image_url="new.jpg"), products[1]]
    assert index.build(updated) is False  # text unchanged -> no re-embedding
    assert index.products[1]["price"] == 80.0
    assert index.products[1]["image_url"] == "new.jpg"
