WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    "low":    {"goal": 0.30, "liquidity": 0.25, "risk": 0.35, "tax": 0.10},
    "medium": {"goal": 0.40, "liquidity": 0.20, "risk": 0.25, "tax": 0.15},
    "high":   {"goal": 0.50, "liquidity": 0.15, "risk": 0.20, "tax": 0.15},
}

TAX_DELTA_PLACEHOLDER = 0.0


def score_action(deltas: dict[str, float], risk_profile: str = "medium") -> float:
    """Compute a weighted composite score adapted to the user's risk profile.

    Low-risk users weight risk reduction more heavily.
    High-risk users weight goal progress more heavily.
    """
    w = WEIGHT_PROFILES.get(risk_profile, WEIGHT_PROFILES["medium"])

    return (
        deltas["goal_delta"] * w["goal"]
        + deltas["liquidity_delta"] * w["liquidity"]
        + deltas["risk_delta"] * w["risk"]
        + TAX_DELTA_PLACEHOLDER * w["tax"]
    )


def get_weights(risk_profile: str = "medium") -> dict[str, float]:
    """Return the weight profile for display/transparency."""
    return WEIGHT_PROFILES.get(risk_profile, WEIGHT_PROFILES["medium"])
