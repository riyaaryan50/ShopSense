
import math
from collections import Counter


# Original weights are retained as baseline knowledge.
BASE_EVENT_WEIGHTS = {
    "view": 1.0,
    "click": 1.5,
    "wishlist": 2.5,
    "cart": 3.0,
    "purchase": 5.0,
}


def fuzzy_memberships(value):
    """
    Calculate fuzzy membership values for:
    Low, Medium and High interaction frequency.

    Input value must be between 0 and 1.
    """

    value = max(0.0, min(1.0, value))

    low = max(0.0, 1.0 - 2.0 * value)

    medium = max(
        0.0,
        1.0 - abs(2.0 * value - 1.0)
    )

    high = max(0.0, 2.0 * value - 1.0)

    return {
        "low": low,
        "medium": medium,
        "high": high,
    }


def calculate_adaptive_event_weights(interactions):
    """
    Calculate user-specific adaptive interaction weights.

    Uses:
    1. Original baseline weights
    2. Fuzzy membership functions
    3. Interaction frequency
    4. Confidence based on history size

    Returns adaptive weights for each event.
    """

    event_counts = Counter()

    valid_events = set(BASE_EVENT_WEIGHTS.keys())

    for interaction in interactions:

        event_type = interaction.get("event_type")

        if event_type in valid_events:
            event_counts[event_type] += 1

    total_interactions = sum(event_counts.values())

    # Insufficient history:
    # Retain original weights.

    if total_interactions == 0:
        return BASE_EVENT_WEIGHTS.copy()

    # Confidence increases as interaction history grows.

    confidence = (
        total_interactions /
        (total_interactions + 10.0)
    )

    adaptive_weights = {}

    # Maximum adjustment is limited to 10%.

    max_adjustment = 0.10

    for event_type, base_weight in BASE_EVENT_WEIGHTS.items():

        count = event_counts[event_type]

        # Keep baseline weight if event has never occurred.

        if count == 0:
            adaptive_weights[event_type] = base_weight
            continue

        # Convert frequency into a value between 0 and 1.

        frequency = count / (count + 3.0)

        memberships = fuzzy_memberships(frequency)

        # Defuzzification using weighted membership values.

        fuzzy_interest = (
            0.2 * memberships["low"]
            + 0.6 * memberships["medium"]
            + 1.0 * memberships["high"]
        )

        # Convert fuzzy interest into an adaptive multiplier.

        adjustment = (
            max_adjustment
            * confidence
            * (2.0 * fuzzy_interest - 1.0)
        )

        multiplier = 1.0 + adjustment

        adaptive_weights[event_type] = (
            base_weight * multiplier
        )

    return adaptive_weights
