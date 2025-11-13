"""Opportunity scoring utilities."""


def calculate_tier(value_score: float, config: dict) -> str:
    """Calculate opportunity tier based on value score."""
    thresholds = config.get("thresholds", {})

    tier_s = thresholds.get("tier_s_threshold", 9.0)
    tier_a = thresholds.get("tier_a_threshold", 7.5)
    tier_b = thresholds.get("tier_b_threshold", 6.0)

    if value_score >= tier_s:
        return "S"
    elif value_score >= tier_a:
        return "A"
    elif value_score >= tier_b:
        return "B"
    elif value_score >= 4.0:
        return "C"
    else:
        return "D"
