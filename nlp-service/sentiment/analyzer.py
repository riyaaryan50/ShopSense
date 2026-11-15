"""VADER sentiment analysis for customer reviews.

compound >  0.05  -> positive
compound < -0.05  -> negative
otherwise         -> neutral
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

import config
from common.text_cleaning import light_clean


def label_from_compound(compound):
    if compound > config.POSITIVE_THRESHOLD:
        return "positive"
    if compound < config.NEGATIVE_THRESHOLD:
        return "negative"
    return "neutral"


def label_from_rating(rating):
    """Star-rating ground truth used for benchmarking (4-5 / 3 / 1-2)."""
    if rating is None:
        return None
    rating = int(rating)
    if rating >= 4:
        return "positive"
    if rating <= 2:
        return "negative"
    return "neutral"


# VADER's lexicon is tuned for social media. Product reviews describe defects
# with words it scores as neutral ("expensive", "broke", "lags", "leaks").
# These e-commerce terms are added on top of the stock lexicon; the benchmark
# reports accuracy with and without them.
#
# Context-dependent words ("hot" in "keeps tea hot", "heavy", "loud", "cheap")
# are deliberately left out, and weights are scaled by DOMAIN_SCALE: at full
# strength, 4-star "Only downside: ..." reviews flipped negative. With 0.7 the
# overall accuracy equals plain VADER while clearly-negative products (e.g.
# "ink cartridges are expensive") are no longer reported as positive.
# NOTE: tuned on the synthetic demo reviews – re-check on real reviews.
DOMAIN_SCALE = 0.7
DOMAIN_LEXICON = {
    "expensive": -1.6, "overpriced": -2.0, "broke": -2.2, "broken": -2.2,
    "cracked": -1.9, "lags": -1.6, "lag": -1.4, "laggy": -1.8, "stutters": -1.6,
    "slow": -1.3, "slower": -1.2, "slowly": -1.0, "drains": -1.5, "dies": -1.8,
    "leaks": -1.9, "leaked": -1.9, "leak": -1.6, "flimsy": -1.7, "wobbly": -1.4,
    "wobbles": -1.4, "noisy": -1.3, "heats": -1.4,
    "overheats": -2.0, "grainy": -1.3, "dull": -1.2, "dim": -1.0, "mushy": -1.2,
    "faded": -1.1, "fading": -1.1, "streaky": -1.4, "jams": -1.5, "jam": -1.2,
    "drops": -1.2, "flickers": -1.4, "loosens": -1.2, "loose": -1.0, "loosely": -1.0,
    "tinny": -1.4, "muddy": -1.3, "distorts": -1.5, "uncomfortable": -1.8,
    "hurt": -1.8, "cramps": -1.5, "useless": -2.4, "unreliable": -1.8,
    "unresponsive": -1.7, "corrupted": -2.2, "frustrating": -2.0, "annoying": -1.7,
    "bulky": -1.1, "harsh": -1.3,
    "snappy": 1.6, "smoothly": 1.4, "sturdy": 1.6, "durable": 1.6, "reliable": 1.7,
    "crisp": 1.4, "vivid": 1.4, "handy": 1.3, "convenient": 1.4, "responsive": 1.4,
    "affordable": 1.3,
}


class SentimentAnalyzer:
    name = "vader+domain-lexicon"

    def __init__(self, domain_lexicon=True):
        self._vader = SentimentIntensityAnalyzer()
        if domain_lexicon:
            self._vader.lexicon.update(
                {word: weight * DOMAIN_SCALE for word, weight in DOMAIN_LEXICON.items()})
        else:
            self.name = "vader"

    def analyze(self, text):
        # Light cleaning only: VADER uses capitalisation, "!!!" and emoticons.
        scores = self._vader.polarity_scores(light_clean(text))
        return {
            "compound": round(scores["compound"], 4),
            "positive": round(scores["pos"], 4),
            "negative": round(scores["neg"], 4),
            "neutral": round(scores["neu"], 4),
            "label": label_from_compound(scores["compound"]),
        }

    def label(self, text):
        return self.analyze(text)["label"]
