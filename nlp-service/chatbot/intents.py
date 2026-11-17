"""Rule-based intent classifier + entity extraction for the shopping assistant.

Intents (from the sprint plan, plus ``help``):
    greeting, help, compare_products, review_summary, get_recommendation,
    product_info, search_product (default), fallback

Entities:
    products  – catalogue products named in the message (fuzzy, model-number aware)
    category  – catalogue category implied by keywords ("earbuds" -> Audio)
    budget    – {"min": .., "max": ..} parsed from "under 5k", "between 2000 and 4000"
    query     – the message with filler/budget words removed (fed to semantic search)
"""

import re
from collections import Counter
from dataclasses import dataclass, field

from common.text_cleaning import clean_text, tokenize

# ---------------------------------------------------------------------- #
# Patterns
# ---------------------------------------------------------------------- #
GREETING_RE = re.compile(
    r"^\s*(hi+|hello+|hey+|hiya|namaste|howdy|yo|good\s+(morning|afternoon|evening))"
    r"\b[\s,!.]*(there|shopsense|bot|assistant)?[\s!.]*$", re.I)
THANKS_RE = re.compile(
    r"^\s*(thanks|thank\s+you|thx|ty|cheers|bye|goodbye|see\s+you|ok(ay)?\s+thanks?)\b", re.I)
HELP_RE = re.compile(
    r"\b(help|what\s+can\s+you\s+do|how\s+(do|does)\s+(this|you)\s+work|what\s+do\s+you\s+do)\b", re.I)
COMPARE_RE = re.compile(
    r"\b(compare|comparison|versus|vs\.?|difference\s+between|differences|which\s+(one\s+)?is\s+better|"
    r"better\s+than)\b", re.I)
REVIEW_RE = re.compile(
    r"\b(reviews?|reviewed|opinions?|feedback|ratings?|sentiment|complain\w*|pros\s+and\s+cons|"
    r"(people|customers?|users?|buyers?)\s+(say|think|feel|said)|"
    r"what\s+do\s+(people|customers|users|buyers)|worth\s+(it|buying)|any\s+good|"
    r"is\s+(it|this|that)\s+good)\b", re.I)
RECOMMEND_RE = re.compile(
    r"\b(recommend\w*|suggest\w*|suggestions?|what\s+should\s+i\s+(buy|get)|"
    r"ideas?|gifts?|personali[sz]ed|for\s+me|my\s+picks?)\b", re.I)
INFO_RE = re.compile(
    r"\b(price|cost|costs|how\s+much|specs?|specifications?|details?|tell\s+me\s+(more\s+)?about|"
    r"info|information|features?|battery|warranty|weight|display|processor|ram|memory|"
    r"storage|capacity|describe|what\s+is|what's)\b", re.I)
PRONOUN_RE = re.compile(r"\b(it|this|that|these|those|them|they|the\s+first|the\s+second|both)\b", re.I)

CATEGORY_PATTERNS = [
    # Most specific first: "laptop backpack" is a backpack, "phone stand" a study item.
    ("Backpacks", r"\b(back\s?packs?|bags?|rucksacks?)\b"),
    ("Study Essentials", r"\b(calculators?|lamps?|desk\s+lights?|study\s+lights?|printers?|"
                         r"(phone|mobile)\s+stands?|stands?)\b"),
    ("Hostel Essentials", r"\b(kettles?|power\s?banks?|bottles?|flasks?|extension(\s+boards?)?|"
                          r"power\s+(strips?|extenders?|plates?)|surge)\b"),
    ("Storage & Data", r"\b(pen\s?drives?|flash\s?drives?|usb\s+drives?|usb\s+sticks?|storage\s+devices?)\b"),
    ("Computer Accessories", r"\b(mouse|mice|keyboards?)\b"),
    ("Audio", r"\b(head\s?phones?|ear\s?phones?|ear\s?buds?|headsets?|audio|music|speakers?|tws)\b"),
    ("Tablets", r"\b(tablets?|tabs?|ipads?)\b"),
    ("Smartphones", r"\b(smart\s?phones?|phones?|mobiles?|5g)\b"),
    ("Laptops", r"\b(laptops?|notebooks?|computers?|pcs?)\b"),
]
CATEGORY_PATTERNS = [(name, re.compile(p, re.I)) for name, p in CATEGORY_PATTERNS]

_NUM = r"(?:rs\.?|inr|₹)?\s*(\d[\d,]*(?:\.\d+)?)\s*(k|thousand)?\b"
BETWEEN_RE = re.compile(r"\bbetween\s+" + _NUM + r"\s*(?:and|to|-)\s*" + _NUM, re.I)
MAX_RE = re.compile(
    r"\b(?:under|below|less\s+than|cheaper\s+than|within|upto|up\s+to|max(?:imum)?|"
    r"budget(?:\s+(?:of|is))?|not\s+more\s+than)\s*" + _NUM, re.I)
MIN_RE = re.compile(r"\b(?:above|over|more\s+than|at\s+least|minimum)\s*" + _NUM, re.I)

FILLER_RE = re.compile(
    r"\b(please|pls|can\s+you|could\s+you|would\s+you|show\s+me|find\s+me|find|search\s+for|search|"
    r"looking\s+for|look\s+for|i\s+need|i\s+want|i'?m\s+looking\s+for|get\s+me|give\s+me|"
    r"do\s+you\s+have|any|some|recommend\w*|suggest\w*|suggestions?|for\s+me|"
    r"what\s+should\s+i\s+(buy|get)|good|best|a|an|the|me|products?|items?|something|"
    r"options?|ideas?)\b", re.I)

# Tokens that appear in product names but say nothing about *which* product.
GENERIC_TOKENS = {
    "wireless", "with", "and", "the", "for", "in", "of", "on", "plus", "pro", "wi",
    "fi", "gb", "mah", "ml", "inch", "new", "all", "one", "combo", "silent",
    "adjustable", "electric", "usb", "power",
}


def _singular(token):
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _norm_tokens(text):
    # "A9+" and "A9" are different products, so keep the plus as part of the
    # model token ("a9plus") instead of letting tokenisation drop it.
    text = re.sub(r"(?<=\w)\+", "plus", str(text or "").lower())
    text = re.sub(r"\s+plus\b", "plus", text)  # "A9 Plus" -> "a9plus" too
    tokens = tokenize(text) + tokenize(text.replace("-", ""))
    return {_singular(t) for t in tokens}


def _to_number(value, suffix):
    number = float(value.replace(",", ""))
    if suffix:
        number *= 1000
    return number


def extract_budget(text):
    budget = {"min": None, "max": None}
    match = BETWEEN_RE.search(text)
    if match:
        low = _to_number(match.group(1), match.group(2))
        high = _to_number(match.group(3), match.group(4))
        budget["min"], budget["max"] = min(low, high), max(low, high)
        return budget
    match = MAX_RE.search(text)
    if match:
        budget["max"] = _to_number(match.group(1), match.group(2))
    match = MIN_RE.search(text)
    if match:
        budget["min"] = _to_number(match.group(1), match.group(2))
    return budget


def strip_budget(text):
    for pattern in (BETWEEN_RE, MAX_RE, MIN_RE):
        text = pattern.sub(" ", text)
    return text


def extract_category(text):
    for name, pattern in CATEGORY_PATTERNS:
        if pattern.search(text):
            return name
    return None


# ---------------------------------------------------------------------- #
# Product mention matcher
# ---------------------------------------------------------------------- #
class ProductMatcher:
    """Finds catalogue products named in free text.

    Each name token is weighted by how *identifying* it is:
      model numbers unique to one product (ch520, a9, mk270r) ... 3.0
      words unique to one product name (rockerz, ideapad, kettle)  2.0
      the brand                                                    1.5 / 1.0
      words shared by several products (headphones, backpack)      0.5
      generic words (wireless, with, usb)                          0
    A product is "mentioned" when its score reaches ``threshold``.
    """

    def __init__(self, products, threshold=1.5):
        self.threshold = threshold
        self.products = {int(p["id"]): p for p in products}
        self.tokens = {}
        doc_freq = Counter()
        for pid, product in self.products.items():
            tokens = _norm_tokens(product["name"]) | _norm_tokens(product.get("category", ""))
            tokens = {t for t in tokens if len(t) > 1 and t not in GENERIC_TOKENS}
            self.tokens[pid] = tokens
            doc_freq.update(tokens)
        self.doc_freq = doc_freq
        self.brands = {
            pid: _singular((p.get("brand") or p["name"].split()[0]).lower())
            for pid, p in self.products.items()
        }
        self.brand_freq = Counter(self.brands.values())

    def _token_weight(self, pid, token):
        df = self.doc_freq[token]
        has_digit = any(c.isdigit() for c in token)
        if has_digit:
            if token.isdigit() and len(token) <= 2:
                return 0.0
            return 3.0 if df == 1 else 0.5
        if token == self.brands[pid]:
            return 1.5 if self.brand_freq[token] == 1 else 1.0
        return 2.0 if df == 1 else 0.5

    def score_all(self, text):
        message_tokens = _norm_tokens(text)
        scores = {}
        for pid, tokens in self.tokens.items():
            matched = tokens & message_tokens
            if not matched:
                continue
            score = sum(self._token_weight(pid, t) for t in matched)
            coverage = len(matched) / max(len(tokens), 1)
            scores[pid] = (score, coverage)
        return scores

    def find(self, text, limit=3):
        scores = self.score_all(text)
        ranked = sorted(
            (item for item in scores.items() if item[1][0] >= self.threshold),
            key=lambda item: (item[1][0], item[1][1]),
            reverse=True,
        )
        if not ranked:
            return []
        best = ranked[0][1][0]
        # Keep products close to the best match (ties) – drop weak extras.
        return [pid for pid, (score, _) in ranked if score >= best * 0.75][:limit]

    def find_for_comparison(self, text):
        """Split "A vs B" / "A or B" / "A and B" and match each side separately."""
        body = re.sub(r"^.*?\b(compare|between)\b", "", text, flags=re.I) or text
        parts = re.split(r"\bvs\.?\b|\bversus\b|\bor\b|\band\b|\bwith\b|,|/", body, flags=re.I)
        found = []
        for part in parts:
            for pid in self.find(part, limit=1):
                if pid not in found:
                    found.append(pid)
        if len(found) < 2:
            for pid in self.find(text, limit=3):
                if pid not in found:
                    found.append(pid)
        return found[:3]

    def coverage_of_message(self, text, pid):
        """(share of message words that belong to the product name, matched count)."""
        message = {t for t in _norm_tokens(clean_text(FILLER_RE.sub(" ", text)))
                   if len(t) > 1}
        if not message:
            return 0.0, 0
        matched = len(message & self.tokens.get(pid, set()))
        return matched / len(message), matched


# ---------------------------------------------------------------------- #
# Classifier
# ---------------------------------------------------------------------- #
@dataclass
class Intent:
    name: str
    confidence: float
    entities: dict = field(default_factory=dict)

    def to_dict(self):
        return {"intent": self.name, "confidence": self.confidence,
                "entities": self.entities}


class IntentClassifier:
    def __init__(self, products):
        self.matcher = ProductMatcher(products)

    def refresh(self, products):
        self.matcher = ProductMatcher(products)

    def extract_entities(self, message, compare=False):
        budget = extract_budget(message)
        products = (self.matcher.find_for_comparison(message) if compare
                    else self.matcher.find(message))
        query = clean_text(FILLER_RE.sub(" ", strip_budget(message)))
        return {
            "products": products,
            "category": extract_category(message),
            "budget": budget,
            "query": query,
            "uses_pronoun": bool(PRONOUN_RE.search(message)),
        }

    def classify(self, message):
        text = (message or "").strip()
        if not text:
            return Intent("fallback", 1.0, {})

        if GREETING_RE.match(text):
            return Intent("greeting", 0.95, {"kind": "hello"})
        if THANKS_RE.match(text) and len(tokenize(text)) <= 5:
            return Intent("greeting", 0.9, {"kind": "thanks"})
        if HELP_RE.search(text) and len(tokenize(text)) <= 8:
            return Intent("help", 0.9, {})

        if COMPARE_RE.search(text):
            return Intent("compare_products", 0.9, self.extract_entities(text, compare=True))

        entities = self.extract_entities(text)

        if REVIEW_RE.search(text):
            return Intent("review_summary", 0.85, entities)

        if RECOMMEND_RE.search(text):
            return Intent("get_recommendation", 0.85, entities)

        if entities["products"]:
            pid = entities["products"][0]
            coverage, matched = self.matcher.coverage_of_message(text, pid)
            # A bare product name ("Wipro Garnet lamp") is a request for info;
            # a one-word category phrase ("power bank") is a search.
            if INFO_RE.search(text) or (coverage >= 0.5 and matched >= 2):
                return Intent("product_info", 0.8, entities)

        if INFO_RE.search(text) and entities["uses_pronoun"]:
            return Intent("product_info", 0.6, entities)

        content = [t for t in tokenize(entities["query"]) if len(t) > 1]
        if not content and not entities["category"]:
            return Intent("fallback", 0.5, entities)

        return Intent("search_product", 0.7, entities)
