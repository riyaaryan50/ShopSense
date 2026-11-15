from common.text_cleaning import clean_text, light_clean, product_text
from sentiment.analyzer import SentimentAnalyzer, label_from_compound, label_from_rating
from sentiment.summary import extract_themes, summarize_reviews


def test_clean_text_strips_html_urls_and_special_chars():
    raw = "<p>Great &amp; FAST!!</p> Visit https://shop.example.com now :) 15.6-inch"
    assert clean_text(raw) == "great fast visit now 15.6-inch"


def test_light_clean_keeps_case_and_punctuation_for_vader():
    assert light_clean("<b>GREAT</b>   product!!!") == "GREAT product!!!"


def test_product_text_combines_fields_without_price_note():
    text = product_text({
        "name": "Sony WH-CH520", "brand": "Sony", "category": "Audio",
        "description": "Wireless headphones",
        "specifications": {"battery": "50 hours", "price_note": "ignore me"},
    })
    assert "sony wh-ch520" in text and "battery 50 hours" in text
    assert "ignore" not in text


def test_vader_thresholds():
    assert label_from_compound(0.06) == "positive"
    assert label_from_compound(-0.06) == "negative"
    assert label_from_compound(0.05) == "neutral"
    assert label_from_compound(-0.05) == "neutral"


def test_rating_ground_truth_mapping():
    assert [label_from_rating(r) for r in (1, 2, 3, 4, 5)] == [
        "negative", "negative", "neutral", "positive", "positive"]


def test_analyzer_labels_clear_reviews():
    analyzer = SentimentAnalyzer()
    assert analyzer.label("Absolutely love it, excellent battery life!") == "positive"
    assert analyzer.label("Terrible. It broke in a week, worst purchase ever.") == "negative"


def test_themes_prefer_aspect_bigrams_over_opinion_words():
    texts = ["Battery life is amazing", "Great battery life and sound quality",
             "Sound quality is clear"]
    themes = extract_themes(texts, texts, top_n=3)
    assert "battery life" in themes
    assert "sound quality" in themes
    assert not any(t in ("great", "amazing") for t in themes)


def test_summary_structure_and_counts(services):
    product = services.product(7)
    reviews = services.data.get_reviews(7)
    summary = summarize_reviews(product, reviews, services.analyzer, include_reviews=True)

    assert summary["total_reviews"] == 5
    assert summary["positive_count"] + summary["negative_count"] + summary["neutral_count"] == 5
    assert summary["positive_count"] >= 4
    assert summary["overall_sentiment"] == "positive"
    assert "battery life" in summary["top_positive_themes"]
    assert summary["average_rating"] == 4.0
    assert len(summary["reviews"]) == 5
    assert summary["verdict"].startswith("Customers are largely positive")
    # Product name words are never reported as themes.
    assert not any("sony" in t for t in summary["top_positive_themes"])


def test_summary_negative_product(services):
    summary = services.review_summary(8)
    assert summary["negative_count"] >= 3
    assert summary["overall_sentiment"] == "negative"
    assert any("build" in t for t in summary["top_negative_themes"])


def test_summary_without_reviews(services):
    summary = services.review_summary(2)
    assert summary["total_reviews"] == 0
    assert summary["overall_sentiment"] == "no_reviews"
    assert summary["top_positive_themes"] == []
