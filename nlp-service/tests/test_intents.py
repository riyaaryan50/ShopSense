import pytest

from chatbot.intents import extract_budget, extract_category

# 30 labelled queries (the sprint plan asks for 20+).
LABELLED_QUERIES = [
    ("hi", "greeting"),
    ("Hello there!", "greeting"),
    ("good morning", "greeting"),
    ("thanks a lot", "greeting"),
    ("what can you do?", "help"),
    ("help", "help"),
    ("find me wireless earbuds", "search_product"),
    ("show me laptops under 60000", "search_product"),
    ("I need something to keep my tea hot", "search_product"),
    ("power bank", "search_product"),
    ("looking for a bag for college", "search_product"),
    ("cheap pen drive for project files", "search_product"),
    ("recommend something for me", "get_recommendation"),
    ("suggest wireless headphones under 3000", "get_recommendation"),
    ("what should I buy for my hostel room?", "get_recommendation"),
    ("any gift ideas for an engineering student", "get_recommendation"),
    ("compare Sony WH-CH520 vs boAt Rockerz 430", "compare_products"),
    ("Galaxy Tab A9 versus Tab S9 FE", "compare_products"),
    ("which is better, the ideapad or the hp 15s?", "compare_products"),
    ("difference between the two backpacks", "compare_products"),
    ("what do people say about the Philips kettle?", "review_summary"),
    ("reviews of the HP printer", "review_summary"),
    ("is the Casio calculator worth it?", "review_summary"),
    ("what do customers think about the boat headphones", "review_summary"),
    ("tell me about the Logitech M220", "product_info"),
    ("how much is the Galaxy M36?", "product_info"),
    ("Wipro Garnet lamp", "product_info"),
    ("battery of the Sony WH-CH520", "product_info"),
    ("", "fallback"),
    ("???", "fallback"),
]


@pytest.mark.parametrize("message,expected", LABELLED_QUERIES)
def test_intent_classification(services, message, expected):
    assert services.classifier.classify(message).name == expected


def test_intent_accuracy_summary(services):
    correct = sum(services.classifier.classify(m).name == e for m, e in LABELLED_QUERIES)
    assert correct / len(LABELLED_QUERIES) >= 0.9


@pytest.mark.parametrize("text,expected", [
    ("under 5k", {"min": None, "max": 5000.0}),
    ("below ₹2,500", {"min": None, "max": 2500.0}),
    ("between 2000 and 4000", {"min": 2000.0, "max": 4000.0}),
    ("above rs 10000", {"min": 10000.0, "max": None}),
    ("budget of 1500", {"min": None, "max": 1500.0}),
    ("over-ear headphones", {"min": None, "max": None}),
])
def test_budget_extraction(text, expected):
    assert extract_budget(text) == expected


@pytest.mark.parametrize("text,expected", [
    ("wireless earbuds", "Audio"),
    ("laptop backpack", "Backpacks"),
    ("phone stand for lectures", "Study Essentials"),
    ("power bank for my phone", "Hostel Essentials"),
    ("a laptop for coding", "Laptops"),
    ("something nice", None),
])
def test_category_extraction(text, expected):
    assert extract_category(text) == expected


@pytest.mark.parametrize("text,expected_ids", [
    ("compare galaxy tab a9 vs tab s9 fe", [4, 5]),
    ("compare sony and boat headphones", [7, 8]),
    ("which is better, the ideapad or the hp 15s?", [2, 3]),
])
def test_product_matching_for_comparison(services, text, expected_ids):
    entities = services.classifier.extract_entities(text, compare=True)
    assert entities["products"][:2] == expected_ids


@pytest.mark.parametrize("text,expected_id", [
    ("the Sony WH-CH520", 7),
    ("wh-ch520", 7),
    ("rockerz 430", 8),
    ("the kettle", 13),
    ("Casio fx-991ex", 11),
    ("hp laptop", 3),
])
def test_single_product_matching(services, text, expected_id):
    assert services.classifier.matcher.find(text)[0] == expected_id


def test_generic_words_do_not_match_a_product(services):
    assert services.classifier.matcher.find("wireless earbuds") == []
    assert services.classifier.matcher.find("a laptop") == []
