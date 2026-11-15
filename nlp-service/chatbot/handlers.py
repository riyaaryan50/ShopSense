"""Chatbot engine: classify intent -> run handler -> structured JSON response.

Every response has the same shape so the React widget can render it:

    {
      "intent": "search_product", "confidence": 0.7, "type": "products",
      "text": "...",                       # always present
      "products": [card, ...],             # product cards (optional)
      "comparison": {...},                 # side-by-side table (optional)
      "summary": {...},                    # review summary (optional)
      "suggestions": ["...", "..."],       # quick-reply chips
      "entities": {...}
    }
"""

import logging

from common.services import product_card

log = logging.getLogger(__name__)

# Below this cosine score a search result is considered irrelevant.
MIN_RELEVANCE = {"tfidf-fallback": 0.05}
DEFAULT_MIN_RELEVANCE = 0.22

COMPARE_SPEC_KEYS = [
    "processor", "memory", "storage", "display", "battery", "battery_life",
    "camera", "connectivity", "capacity", "weight", "warranty",
]


def _price(value):
    return f"₹{value:,.0f}"


def _budget_text(budget):
    if budget.get("min") and budget.get("max"):
        return f" between {_price(budget['min'])} and {_price(budget['max'])}"
    if budget.get("max"):
        return f" under {_price(budget['max'])}"
    if budget.get("min"):
        return f" above {_price(budget['min'])}"
    return ""


class ChatEngine:
    def __init__(self, services):
        self.services = services

    # -------------------------------------------------------------- #
    def respond(self, message, context=None):
        context = context if context is not None else {}
        self.services.sync()
        intent = self.services.classifier.classify(message)
        handler = getattr(self, f"_handle_{intent.name}", self._handle_fallback)
        try:
            response = handler(message, intent.entities, context)
        except Exception:  # noqa: BLE001 - never crash the socket
            log.exception("Chat handler %s failed", intent.name)
            response = {
                "type": "text",
                "text": "Sorry, something went wrong while answering that. "
                        "Please try again in a moment.",
            }
        response.setdefault("products", [])
        response.setdefault("suggestions", [])
        response.update({
            "intent": intent.name,
            "confidence": intent.confidence,
            "entities": intent.entities,
            "message": message,
        })
        shown = [p["id"] for p in response.get("products", [])]
        if response.get("comparison"):
            shown = [p["id"] for p in response["comparison"]["products"]]
        if shown:
            context["last_products"] = shown
        return response

    # -------------------------------------------------------------- #
    # helpers
    # -------------------------------------------------------------- #
    def _min_relevance(self):
        return MIN_RELEVANCE.get(self.services.index.engine, DEFAULT_MIN_RELEVANCE)

    def _card(self, pid, **extra):
        product = self.services.product(pid)
        ratio = self.services.positive_ratio(pid)
        return product_card(
            product,
            positive_percentage=None if ratio is None else round(ratio * 100),
            **extra,
        )

    def _resolve_products(self, entities, context, want=1):
        """Products named in the message, else the ones discussed last."""
        products = list(entities.get("products") or [])
        if len(products) < want and (entities.get("uses_pronoun") or not products):
            for pid in context.get("last_products", []):
                if pid not in products:
                    products.append(pid)
        return products

    def _search(self, entities, top_k=5, boost_reviews=False):
        index = self.services.index
        budget = entities.get("budget") or {}
        query = entities.get("query") or ""
        category = entities.get("category")
        if not query.strip() and category:
            query = category

        hits = index.search(query, top_k=index.size,
                            min_price=budget.get("min"), max_price=budget.get("max"))
        relevant_floor = self._min_relevance()

        ranked = []
        for hit in hits:
            product = self.services.product(hit["product_id"])
            score = hit["score"]
            if category and product.get("category") == category:
                score += 0.15  # keyword category is a strong hint
            if boost_reviews:
                ratio = self.services.positive_ratio(hit["product_id"])
                score = 0.8 * score + 0.2 * (0.5 if ratio is None else ratio)
            ranked.append((score, hit["score"], hit["product_id"]))
        ranked.sort(reverse=True)
        ranked = [r for r in ranked if r[1] >= relevant_floor or
                  (category and self.services.product(r[2]).get("category") == category)]
        return ranked[:top_k]

    # -------------------------------------------------------------- #
    # intents
    # -------------------------------------------------------------- #
    def _handle_greeting(self, message, entities, context):
        name = context.get("user_name")
        if entities.get("kind") == "thanks":
            return {"type": "text",
                    "text": "You're welcome! Ask me any time you need help shopping. 🛍️",
                    "suggestions": ["Recommend something for me", "Show me study essentials"]}
        hello = f"Hi {name}!" if name else "Hi there!"
        return {
            "type": "text",
            "text": f"{hello} I'm the ShopSense AI assistant. I can find products, "
                    "recommend items for you, compare products and summarise what "
                    "customers say in reviews.",
            "suggestions": [
                "Find wireless headphones under 3000",
                "Recommend something for me",
                "Compare Sony WH-CH520 vs boAt Rockerz 430",
                "What do people say about the Philips kettle?",
            ],
        }

    def _handle_help(self, message, entities, context):
        return {
            "type": "text",
            "text": "Here's what I can do:\n"
                    "• Search – \"find a laptop for coding under 60000\"\n"
                    "• Recommend – \"suggest something for hostel life\"\n"
                    "• Compare – \"compare Galaxy Tab A9 and Tab S9 FE\"\n"
                    "• Reviews – \"what do people think about the HP printer?\"\n"
                    "• Product info – \"tell me about the Casio calculator\"",
            "suggestions": ["Show me power banks", "Recommend something for me"],
        }

    def _handle_search_product(self, message, entities, context):
        results = self._search(entities, top_k=5)
        budget = entities.get("budget") or {}
        query_label = entities.get("query") or entities.get("category") or message

        if not results and (budget.get("max") or budget.get("min")):
            # Nothing in budget: show the closest relevant options anyway.
            relaxed = dict(entities, budget={})
            results = self._search(relaxed, top_k=3)
            if results:
                products = [self._card(pid, score=round(raw, 3))
                            for _, raw, pid in results]
                return {
                    "type": "products",
                    "text": f"I couldn't find “{query_label}”{_budget_text(budget)}. "
                            "These are the closest matches outside your budget:",
                    "products": products,
                    "suggestions": [f"Compare {products[0]['name']} and {products[1]['name']}"]
                    if len(products) > 1 else [],
                }

        if not results:
            return self._handle_fallback(message, entities, context)

        products = [self._card(pid, score=round(raw, 3)) for _, raw, pid in results]
        top = products[0]
        suggestions = [f"What do people say about {top['name']}?"]
        if len(products) > 1:
            suggestions.append(f"Compare {products[0]['name']} and {products[1]['name']}")
        return {
            "type": "products",
            "text": f"Here are the best matches for “{query_label}”{_budget_text(budget)}:",
            "products": products,
            "suggestions": suggestions,
        }

    def _handle_get_recommendation(self, message, entities, context):
        query = entities.get("query") or ""
        has_content = any(len(t) > 2 for t in query.split()) or entities.get("category")

        if has_content:
            # "suggest headphones under 3000" -> semantic search ranked by reviews too.
            results = self._search(entities, top_k=4, boost_reviews=True)
            if results:
                products = []
                for _, raw, pid in results:
                    ratio = self.services.positive_ratio(pid)
                    reason = (f"{round(ratio * 100)}% positive reviews"
                              if ratio is not None else "Relevant to your request")
                    products.append(self._card(pid, score=round(raw, 3), reason=reason))
                return {
                    "type": "products",
                    "text": "Based on what you asked for, I'd suggest these "
                            f"(ranked by relevance and customer sentiment){_budget_text(entities.get('budget') or {})}:",
                    "products": products,
                    "suggestions": [f"What do people say about {products[0]['name']}?"],
                }

        return self._personal_recommendations(context)

    def _personal_recommendations(self, context):
        token = context.get("token")
        source_text = None
        items = []
        if token:
            try:
                data = self.services.backend_get("/api/recommendations/me", token=token,
                                                 params={"limit": 5})
                items = data.get("recommendations", [])
                source_text = data.get("explanation")
            except Exception as error:  # noqa: BLE001
                log.warning("Personal recommendations unavailable: %s", error)
        if not items:
            try:
                data = self.services.backend_get("/api/recommendations/popular",
                                                 params={"limit": 5})
                items = data.get("recommendations", [])
                source_text = ("You're not logged in, so here are our most popular products."
                               if not token else "Here are our most popular products right now.")
            except Exception as error:  # noqa: BLE001
                log.warning("Popular recommendations unavailable: %s", error)

        products = []
        for item in items:
            pid = int(item.get("id") or item.get("product_id"))
            if self.services.product(pid):
                products.append(self._card(pid, reason=item.get("reason")))

        if not products:
            # Last resort: best-reviewed products.
            ranked = sorted(self.services.products(),
                            key=lambda pid: self.services.positive_ratio(pid) or 0,
                            reverse=True)[:5]
            products = [self._card(pid, reason="Highly rated by customers") for pid in ranked]
            source_text = "Here are the best-reviewed products in the store."

        return {
            "type": "products",
            "text": source_text or "Here are products picked for you:",
            "products": products,
            "suggestions": ["Find a laptop for coding under 60000", "Show me study essentials"],
        }

    def _handle_compare_products(self, message, entities, context):
        pids = self._resolve_products(entities, context, want=2)

        if len(pids) < 2:
            # "compare laptops" / "compare headphones": use the category's best matches.
            category = entities.get("category")
            if not category and pids:
                category = self.services.product(pids[0]).get("category")
            if category:
                same = [r[2] for r in self._search(
                    dict(entities, query=entities.get("query") or category), top_k=5)
                    if self.services.product(r[2]).get("category") == category]
                for pid in same:
                    if pid not in pids:
                        pids.append(pid)
                    if len(pids) >= 2:
                        break

        if len(pids) < 2:
            return {
                "type": "text",
                "text": "Tell me which two products to compare, e.g. "
                        "“compare Sony WH-CH520 vs boAt Rockerz 430”.",
                "suggestions": ["Compare Galaxy Tab A9 and Tab S9 FE",
                                "Compare the Lenovo IdeaPad and HP 15s"],
            }

        pids = pids[:3]
        products = [self.services.product(pid) for pid in pids]
        summaries = [self.services.review_summary(pid) for pid in pids]
        cards = [self._card(pid) for pid in pids]

        def stars(summary):
            if summary["average_rating"] is None:
                return "No ratings"
            return f"{summary['average_rating']} ★ ({summary['total_reviews']} reviews)"

        rows = [
            {"label": "Price", "values": [_price(p["price"]) for p in products]},
            {"label": "Brand", "values": [p.get("brand") or "—" for p in products]},
            {"label": "Category", "values": [p.get("category") or "—" for p in products]},
            {"label": "Rating", "values": [stars(s) for s in summaries]},
            {"label": "Positive reviews",
             "values": [f"{s['positive_percentage']}%" if s["total_reviews"] else "—"
                        for s in summaries]},
            {"label": "Customers like",
             "values": [", ".join(s["top_positive_themes"][:2]) or "—" for s in summaries]},
            {"label": "Complaints",
             "values": [", ".join(s["top_negative_themes"][:2]) or "—" for s in summaries]},
        ]
        for key in COMPARE_SPEC_KEYS:
            values = [str((p.get("specifications") or {}).get(key, "")) for p in products]
            if sum(1 for v in values if v) >= 2:
                rows.append({"label": key.replace("_", " ").title(),
                             "values": [v or "—" for v in values]})

        cheapest = min(products, key=lambda p: p["price"])
        reviewed = [(s["positive_percentage"], p) for s, p in zip(summaries, products)
                    if s["total_reviews"]]
        verdict = f"{cheapest['name']} is the most affordable at {_price(cheapest['price'])}."
        if reviewed:
            best_pct, best = max(reviewed, key=lambda item: item[0])
            verdict += f" {best['name']} has the best customer sentiment ({best_pct}% positive)."

        return {
            "type": "comparison",
            "text": "Here's a side-by-side comparison:",
            "comparison": {"products": cards, "rows": rows, "verdict": verdict},
            "suggestions": [f"What do people say about {products[0]['name']}?",
                            f"Tell me about {products[1]['name']}"],
        }

    def _find_single_product(self, message, entities, context):
        pids = self._resolve_products(entities, context, want=1)
        if pids:
            return pids[0]
        results = self._search(entities, top_k=1)
        if results and results[0][1] >= self._min_relevance() + 0.15:
            return results[0][2]
        return None

    def _handle_review_summary(self, message, entities, context):
        pid = self._find_single_product(message, entities, context)
        if pid is None:
            return {
                "type": "text",
                "text": "Which product would you like a review summary for? "
                        "For example: “What do people say about the Sony headphones?”",
                "suggestions": ["Reviews of the Philips kettle",
                                "What do people think about the HP printer?"],
            }
        summary = self.services.review_summary(pid)
        product = self.services.product(pid)
        return {
            "type": "review_summary",
            "text": summary["verdict"],
            "summary": summary,
            "products": [self._card(pid)],
            "suggestions": [f"Tell me about {product['name']}",
                            f"Show me alternatives to {product['name']}"],
        }

    def _handle_product_info(self, message, entities, context):
        pid = self._find_single_product(message, entities, context)
        if pid is None:
            return self._handle_search_product(message, entities, context)
        product = self.services.product(pid)
        specs = product.get("specifications") or {}
        highlights = [
            f"{key.replace('_', ' ').title()}: {value}"
            for key, value in specs.items() if key != "price_note"
        ][:6]
        text = (f"{product['name']} by {product.get('brand') or 'unknown brand'} costs "
                f"{_price(product['price'])} ({product.get('category')}).")
        summary = self.services.review_summary(pid)
        if summary and summary["total_reviews"]:
            text += (f" It has {summary['total_reviews']} reviews, "
                     f"{summary['positive_percentage']}% of them positive.")
        similar = self.services.index.similar(pid, top_k=1) or []
        suggestions = [f"What do people say about {product['name']}?"]
        if similar:
            other = self.services.product(similar[0]["product_id"])
            suggestions.append(f"Compare {product['name']} and {other['name']}")
        return {
            "type": "product_info",
            "text": text,
            "details": highlights,
            "products": [self._card(pid)],
            "suggestions": suggestions,
        }

    def _handle_fallback(self, message, entities, context):
        return {
            "type": "text",
            "text": "Sorry, I couldn't find anything for that. Try asking me to find a "
                    "product, recommend something, compare two products or summarise reviews.",
            "suggestions": ["Help", "Show me laptops", "Recommend something for me"],
        }
