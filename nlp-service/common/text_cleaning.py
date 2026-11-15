"""Text cleaning pipeline used by search, sentiment and the chatbot.

Two levels of cleaning are provided on purpose:

* ``clean_text``   – aggressive: lowercase, strip HTML/URLs, remove special
                     characters, normalise whitespace. Used for embeddings,
                     TF-IDF themes and intent matching.
* ``light_clean``  – only strips HTML and normalises whitespace. VADER relies
                     on capitalisation, punctuation ("!!!") and emoticons, so
                     sentiment scoring must NOT use the aggressive version.
"""

import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_SPECIAL_RE = re.compile(r"[^a-z0-9₹\s\-\.]")
_MULTI_SPACE_RE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def strip_html(text):
    """Unescape HTML entities and remove tags."""
    text = html.unescape(str(text or ""))
    return _TAG_RE.sub(" ", text)


def light_clean(text):
    """Remove HTML and extra whitespace but keep case and punctuation."""
    text = strip_html(text)
    text = _URL_RE.sub(" ", text)
    return _MULTI_SPACE_RE.sub(" ", text).strip()


def clean_text(text):
    """Full normalisation for embeddings, keyword extraction and matching."""
    text = strip_html(text).lower()
    text = _URL_RE.sub(" ", text)
    text = text.replace("×", "x")
    text = _SPECIAL_RE.sub(" ", text)
    # Drop dots/hyphens that are not inside a word or number (e.g. "end." ).
    text = re.sub(r"(?<![a-z0-9])[\-\.]|[\-\.](?![a-z0-9])", " ", text)
    return _MULTI_SPACE_RE.sub(" ", text).strip()


def tokenize(text):
    """Lowercase alphanumeric tokens (hyphenated words are split)."""
    return _TOKEN_RE.findall(str(text or "").lower())


def product_text(product):
    """Combine name + brand + category + description + specs into one string.

    This is the document that gets embedded for semantic search.
    """
    specs = product.get("specifications") or {}
    spec_text = " ".join(
        f"{key.replace('_', ' ')} {value}"
        for key, value in specs.items()
        if key not in {"price_note"}
    )
    parts = [
        product.get("name", ""),
        product.get("brand", "") or "",
        product.get("category", "") or "",
        product.get("description", "") or "",
        spec_text,
    ]
    return clean_text(" . ".join(p for p in parts if p))
