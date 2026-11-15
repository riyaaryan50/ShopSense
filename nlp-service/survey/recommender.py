"""Survey-based recommendations (cold-start personalisation).

A new user answers a short onboarding survey on the frontend. The answers are
turned into a natural-language "need statement" which is embedded with the
same MiniLM model as the products, so the survey benefits from semantic
matching rather than plain keyword filters.

score = 0.40 * semantic similarity(need statement, product)
      + 0.25 * category match (interests)
      + 0.20 * budget fit
      + 0.10 * review sentiment (share of positive reviews)
      + 0.05 * brand preference
"""

USE_PHRASES = {
    "online_classes": "attend online classes, video lectures and video calls",
    "coding": "programming and coding practice, needs good processor performance",
    "note_taking": "handwritten notes, pdf annotation with a stylus",
    "music": "listening to music and audio with good sound",
    "hostel_living": "hostel room living and shared accommodation essentials",
    "travel": "travel and daily commute, portable with long battery backup",
    "printing": "printing and scanning assignments and project reports",
    "exam_prep": "exam preparation, engineering maths and science coursework",
    "entertainment": "watching videos, streaming and entertainment",
    "photography": "taking photos and scanning documents with a camera",
}

PRIORITY_PHRASES = {
    "battery": "long battery life",
    "portability": "lightweight, compact and portable",
    "performance": "fast and powerful performance",
    "price": "affordable and value for money",
    "durability": "durable, sturdy build quality",
    "brand": "trusted well-known brand",
    "comfort": "comfortable for long hours",
    "display": "large clear display",
}

ROLE_PHRASES = {
    "school": "a school student",
    "undergrad": "a college undergraduate student",
    "postgrad": "a postgraduate student",
    "professional": "a working professional",
    "other": "a shopper",
}

WEIGHTS = {"semantic": 0.40, "category": 0.25, "budget": 0.20,
           "sentiment": 0.10, "brand": 0.05}


def need_statement(answers):
    """Turn survey answers into text that can be embedded."""
    parts = [f"I am {ROLE_PHRASES.get(answers.get('role'), 'a shopper')}."]
    interests = answers.get("interests") or []
    if interests:
        parts.append("I am interested in " + ", ".join(interests) + ".")
    uses = [USE_PHRASES[u] for u in answers.get("uses") or [] if u in USE_PHRASES]
    if uses:
        parts.append("I will use it for " + "; ".join(uses) + ".")
    priorities = [PRIORITY_PHRASES[p] for p in answers.get("priorities") or []
                  if p in PRIORITY_PHRASES]
    if priorities:
        parts.append("I care about " + ", ".join(priorities) + ".")
    description = (answers.get("description") or "").strip()
    if description:
        parts.append(description)
    return " ".join(parts)


def _budget_fit(price, budget_max, budget_min):
    if budget_max is None or budget_max <= 0:
        return 0.7, None
    if price <= budget_max:
        if budget_min and price < budget_min * 0.5:
            return 0.8, None
        return 1.0, f"Within your ₹{budget_max:,.0f} budget"
    # Smoothly penalise products above budget (half budget over -> ~0.25).
    return max(0.0, (budget_max / price) ** 2), None


def _normalise(values):
    if not values:
        return {}
    low, high = min(values.values()), max(values.values())
    if high - low < 1e-9:
        return {k: 1.0 for k in values}
    return {k: (v - low) / (high - low) for k, v in values.items()}


def survey_recommend(answers, services, top_k=8, exclude_ids=None):
    products = services.products()
    exclude_ids = {int(x) for x in exclude_ids or []}

    statement = need_statement(answers)
    semantic = _normalise(services.index.similarity_to_all(statement))

    interests = {c.lower() for c in answers.get("interests") or []}
    brands = {b.lower() for b in answers.get("brands") or []}
    budget_max = answers.get("budget_max")
    budget_min = answers.get("budget_min")
    budget_max = float(budget_max) if budget_max not in (None, "") else None
    budget_min = float(budget_min) if budget_min not in (None, "") else None
    priorities = answers.get("priorities") or []

    scored = []
    for pid, product in products.items():
        if pid in exclude_ids:
            continue
        reasons = []
        category = (product.get("category") or "").lower()

        category_score = (1.0 if category in interests else 0.0) if interests else 0.5
        if interests and category in interests:
            reasons.append(f"Matches your interest in {product['category']}")

        budget_score, budget_reason = _budget_fit(product["price"], budget_max, budget_min)
        if budget_reason:
            reasons.append(budget_reason)

        brand = (product.get("brand") or "").lower()
        brand_score = (1.0 if brand in brands else 0.0) if brands else 0.5
        if brands and brand in brands:
            reasons.append(f"From {product['brand']}, a brand you prefer")

        ratio = services.positive_ratio(pid)
        sentiment_score = 0.5 if ratio is None else ratio
        if ratio is not None and ratio >= 0.7:
            reasons.append(f"{round(ratio * 100)}% positive customer reviews")

        sem = semantic.get(pid, 0.0)
        if sem >= 0.85:
            reasons.append( "Closely matches what you described")

        breakdown = {
            "semantic": round(sem, 3),
            "category": category_score,
            "budget": round(budget_score, 3),
            "sentiment": round(sentiment_score, 3),
            "brand": brand_score,
        }
        score = sum(WEIGHTS[k] * v for k, v in breakdown.items())
        if priorities and "price" in priorities and budget_max:
            # Price-sensitive users: gently favour cheaper items within budget.
            score += 0.05 * max(0.0, 1 - product["price"] / budget_max)
        scored.append((score, pid, reasons, breakdown))

    scored.sort(key=lambda item: item[0], reverse=True)

    # Diversity: at most 3 products per category in the final list.
    results, per_category = [], {}
    for score, pid, reasons, breakdown in scored:
        category = products[pid].get("category")
        if per_category.get(category, 0) >= 3:
            continue
        per_category[category] = per_category.get(category, 0) + 1
        results.append({
            "product_id": pid,
            "match_score": round(min(score, 1.0) * 100, 1),
            "reasons": reasons[:3] or ["Popular with students like you"],
            "breakdown": breakdown,
        })
        if len(results) >= top_k:
            break

    return {"need_statement": statement, "recommendations": results,
            "weights": WEIGHTS, "engine": services.index.engine}
