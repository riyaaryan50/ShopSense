"""Review summary generation (Day 2 of the plan).

For one product:
    fetch reviews -> VADER on each -> count positive / negative / neutral
    -> TF-IDF keywords on the positive subset and on the negative subset
    -> structured JSON for the frontend and the chatbot.
"""

import re
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

from common.text_cleaning import clean_text, tokenize

# Opinion words carry sentiment but say nothing about *what* customers liked,
# so they are removed before extracting themes ("battery life" is a theme,
# "really good" is not).
OPINION_WORDS = {
    "good", "great", "bad", "nice", "excellent", "amazing", "awesome", "poor",
    "terrible", "worst", "best", "love", "loved", "like", "liked", "hate",
    "really", "very", "quite", "product", "item", "buy", "bought", "purchase",
    "purchased", "money", "worth", "recommend", "recommended", "overall", "just",
    "definitely", "pretty", "bit", "little", "lot", "thing", "things", "using",
    "use", "used", "one", "would", "could", "also", "get", "got", "much",
    "well", "okay", "ok", "fine", "decent", "happy", "disappointed", "perfect",
    "fantastic", "superb", "horrible", "awful", "issue", "issues", "problem",
    "problems", "days", "day", "week", "weeks", "month", "months", "time",
    "far", "still", "even", "though", "however", "expected", "expect",
    "satisfied", "impressed", "glad", "sadly", "unfortunately", "within",
    "star", "stars", "price", "students", "student", "college",
    "easily", "feels", "feel", "look", "looks", "lasts", "last", "downside",
    "average", "only", "gb", "semester", "makes", "make", "keeps", "works",
    "need", "needed", "comes", "came", "enough", "every", "full", "long",
    "absolutely", "highly", "completely", "solid", "choice", "value",
    "mixed", "feelings", "disappointing", "doesn",
    "exceeded", "expectations", "improvement", "needs", "everyday", "average",
    "did", "meet", "better", "ease",
    "run", "runs", "quickly", "kept", "keep", "gets", "goes", "went", "comes",
    "started", "takes", "took", "slightly", "lot", "times", "fits",
    "experience", "satisfied", "superb", "excellent",
}
STOP_WORDS = list(ENGLISH_STOP_WORDS | OPINION_WORDS)


def _name_terms(product):
    """Brand and model-number tokens – excluded from themes.

    Ordinary name words stay: "ink" in "DeskJet Ink Advantage" is exactly
    what customers complain about ("ink cartridges").
    """
    if not product:
        return set()
    brand = set(tokenize(product.get("brand", "")))
    models = {t for t in tokenize(product.get("name", "")) if any(c.isdigit() for c in t)}
    return brand | models


_STOP = set(STOP_WORDS)
_WORD_RE = re.compile(r"[a-z][a-z0-9]+")


def _ngrams(text):
    """Unigrams + bigrams of *adjacent* words, skipping stop/opinion words.

    sklearn's built-in analyzer removes stop words before forming bigrams, which
    invents phrases that nobody wrote ("run out quickly" -> "run quickly").
    """
    grams = []
    # Bigrams never cross sentence or clause boundaries.
    for clause in re.split(r"[.!?;:,()]+", str(text or "").lower()):
        words = _WORD_RE.findall(clean_text(clause))
        grams += [w for w in words if w not in _STOP]
        grams += [f"{a} {b}" for a, b in zip(words, words[1:])
                  if a not in _STOP and b not in _STOP]
    return grams


def extract_themes(subset_texts, all_texts, exclude=None, top_n=5, other_texts=None):
    """Top TF-IDF n-grams of ``subset_texts`` (IDF learnt on ``all_texts``).

    * bigrams are preferred because they are more descriptive ("sound quality")
    * a term frequent in ``other_texts`` (the opposite sentiment) is penalised,
      so a theme only appears on the side where it is characteristic
    * unigrams already covered by a chosen bigram are skipped
    """
    subset = [t for t in subset_texts if t and t.strip()]
    corpus = [t for t in all_texts if t and t.strip()]
    if not subset or not corpus:
        return []

    vectorizer = TfidfVectorizer(analyzer=_ngrams, sublinear_tf=True)
    try:
        vectorizer.fit(corpus)
    except ValueError:  # every word was a stop word
        return []

    matrix = vectorizer.transform(subset)
    scores = np.asarray(matrix.sum(axis=0)).ravel() / len(subset)
    doc_freq = np.asarray((matrix > 0).sum(axis=0)).ravel()
    other = [t for t in (other_texts or []) if t and t.strip()]
    other_scores = (np.asarray(vectorizer.transform(other).sum(axis=0)).ravel() / len(other)
                    if other else np.zeros_like(scores))
    terms = vectorizer.get_feature_names_out()

    exclude = set(exclude or [])
    ranked = []
    for term, score, other_score, df in zip(terms, scores, other_scores, doc_freq):
        if score <= 0:
            continue
        words = term.split()
        if any(w in exclude for w in words):
            continue
        if len(words) == 1 and (df < 2 or term.endswith("ly")):
            continue  # single-mention single words are noise
        weight = (score - 0.8 * other_score) * (2.0 if len(words) > 1 else 1.0)
        weight *= 1.0 + 0.35 * (df - 1)  # mentioned by several reviewers
        if weight > 0:
            ranked.append((weight, term))
    ranked.sort(reverse=True)

    themes = []
    for _, term in ranked:
        words = term.split()
        if len(words) == 1 and any(word in t.split() for t in themes for word in words):
            continue
        if len(words) > 1 and any(t in words for t in themes):
            themes = [t for t in themes if t not in words]
        if len(words) > 1 and any(set(words) & set(t.split()) for t in themes if len(t.split()) > 1):
            continue  # "cartridges expensive" after "ink cartridges"
        themes.append(term)
        if len(themes) >= top_n:
            break
    return themes


def _verdict(summary, product_name):
    total = summary["total_reviews"]
    if total == 0:
        return f"No customer reviews yet for {product_name}."
    pos_pct = summary["positive_percentage"]
    likes = ", ".join(summary["top_positive_themes"][:3])
    dislikes = ", ".join(summary["top_negative_themes"][:2])

    if summary["overall_sentiment"] == "positive":
        text = f"Customers are largely positive about {product_name} ({pos_pct}% positive)."
    elif summary["overall_sentiment"] == "negative":
        text = f"Customers are mostly unhappy with {product_name} (only {pos_pct}% positive)."
    else:
        text = f"Customer opinion on {product_name} is mixed ({pos_pct}% positive)."
    if likes:
        text += f" Praised for: {likes}."
    if dislikes:
        text += f" Common complaints: {dislikes}."
    return text


# Leading bracketed labels such as "[Synthetic demo review]" are metadata, not
# opinion: they must not become "themes" or move the sentiment score.
_LABEL_RE = re.compile(r"^\s*(\[[^\]]{1,60}\]\s*)+")


def strip_labels(text):
    return _LABEL_RE.sub("", text or "")


def summarize_reviews(product, reviews, analyzer, top_n=5, include_reviews=False):
    product_name = (product or {}).get("name", "this product")
    analysed = []
    for review in reviews:
        text = strip_labels(review.get("comment") or "")
        if not text.strip():
            continue
        result = analyzer.analyze(text)
        analysed.append({**review, "text": text, "sentiment": result["label"],
                         "compound": result["compound"]})

    counts = Counter(r["sentiment"] for r in analysed)
    total = len(analysed)
    pos, neg, neu = counts["positive"], counts["negative"], counts["neutral"]

    def pct(n):
        return round(100 * n / total, 1) if total else 0.0

    avg_compound = round(float(np.mean([r["compound"] for r in analysed])), 4) if analysed else 0.0
    ratings = [r["rating"] for r in reviews if r.get("rating") is not None]
    avg_rating = round(float(np.mean(ratings)), 2) if ratings else None

    if total == 0:
        overall = "no_reviews"
    elif pos / total >= 0.6 and avg_compound > 0.05:
        overall = "positive"
    elif neg / total >= 0.5 or avg_compound < -0.05:
        overall = "negative"
    else:
        overall = "mixed"

    all_texts = [r["text"] for r in analysed]
    positive_texts = [r["text"] for r in analysed if r["sentiment"] == "positive"]
    negative_texts = [r["text"] for r in analysed if r["sentiment"] == "negative"]
    exclude = _name_terms(product)
    summary = {
        "product_id": (product or {}).get("id"),
        "product_name": product_name,
        "total_reviews": total,
        "positive_count": pos,
        "negative_count": neg,
        "neutral_count": neu,
        "positive_percentage": pct(pos),
        "negative_percentage": pct(neg),
        "neutral_percentage": pct(neu),
        "average_compound": avg_compound,
        "average_rating": avg_rating,
        "overall_sentiment": overall,
        "top_positive_themes": extract_themes(
            positive_texts, all_texts, exclude, top_n, other_texts=negative_texts),
        "top_negative_themes": extract_themes(
            negative_texts, all_texts, exclude, top_n, other_texts=positive_texts),
        "model": analyzer.name,
    }

    if analysed:
        best = max(analysed, key=lambda r: r["compound"])
        worst = min(analysed, key=lambda r: r["compound"])
        summary["highlights"] = {
            "most_positive": best["comment"] if best["sentiment"] == "positive" else None,
            "most_negative": worst["comment"] if worst["sentiment"] == "negative" else None,
        }
    else:
        summary["highlights"] = {"most_positive": None, "most_negative": None}

    summary["verdict"] = _verdict(summary, product_name)

    if include_reviews:
        summary["reviews"] = [
            {k: r.get(k) for k in ("id", "rating", "comment", "created_at",
                                   "sentiment", "compound")}
            for r in analysed
        ]
    return summary
