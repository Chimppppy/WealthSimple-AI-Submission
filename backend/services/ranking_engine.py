from backend.models.action import Action, ScoredAction
from backend.models.user_profile import UserProfile
from backend.models.financial_state import FinancialState
from backend.models.response import TopRecommendation
from backend.services.action_generator import generate_candidate_actions
from backend.services.simulation_engine import simulate_action
from backend.services.action_scorer import score_action


def rank_actions(
    profile: UserProfile, state: FinancialState
) -> tuple[list[ScoredAction], TopRecommendation]:
    """Generate, simulate, score, normalize, and rank all candidate actions.

    Returns ranked ScoredActions (0-1 normalized) and a TopRecommendation.
    """
    actions = generate_candidate_actions(profile, state)
    raw_results: list[tuple[Action, dict[str, float], float]] = []

    for action in actions:
        deltas = simulate_action(profile, action)
        raw_score = score_action(deltas, profile.risk_profile)
        raw_results.append((action, deltas, raw_score))

    scores = [r[2] for r in raw_results]
    min_score = min(scores)
    max_score = max(scores)
    score_range = max_score - min_score

    scored: list[ScoredAction] = []
    for action, deltas, raw in raw_results:
        normalized = (raw - min_score) / score_range if score_range != 0 else 0.5
        rationale = _build_rationale(action, deltas)
        scored.append(ScoredAction(
            name=action.name,
            description=action.description,
            goal_delta=deltas["goal_delta"],
            liquidity_delta=deltas["liquidity_delta"],
            risk_delta=deltas["risk_delta"],
            total_score=round(normalized, 4),
            rationale=rationale,
        ))

    scored.sort(key=lambda s: s.total_score, reverse=True)

    top = scored[0]
    recommendation = TopRecommendation(
        action=top.name,
        impact_summary=_impact_summary(top),
        tradeoff=_tradeoff_summary(top),
    )

    return scored, recommendation


def _build_rationale(action: Action, deltas: dict[str, float]) -> str:
    """Generate a concise rationale for why this action scored as it did."""
    parts: list[str] = []

    gd = deltas["goal_delta"]
    ld = deltas["liquidity_delta"]
    rd = deltas["risk_delta"]

    if gd > 0.01:
        parts.append(f"improves goal probability by {gd:+.1%}")
    elif gd < -0.01:
        parts.append(f"reduces goal probability by {gd:+.1%}")

    if ld > 0.1:
        parts.append(f"adds {ld:+.1f} months of liquidity")
    elif ld < -0.1:
        parts.append(f"reduces liquidity by {abs(ld):.1f} months")

    if rd > 0.01:
        parts.append(f"reduces risk exposure by {rd:+.1%}")
    elif rd < -0.01:
        parts.append(f"increases risk exposure by {abs(rd):.1%}")

    if not parts:
        return "Marginal impact under current conditions."

    return "This action " + ", ".join(parts) + "."


def _impact_summary(top: ScoredAction) -> str:
    """Summarize the headline impact of the top action."""
    effects: list[str] = []

    if abs(top.goal_delta) > 0.001:
        effects.append(f"goal probability {top.goal_delta:+.1%}")
    if abs(top.liquidity_delta) > 0.01:
        effects.append(f"liquidity {top.liquidity_delta:+.1f} months")
    if abs(top.risk_delta) > 0.001:
        effects.append(f"risk {top.risk_delta:+.1%}")

    if not effects:
        return "Maintains current trajectory with minimal disruption."

    return "Projected impact: " + ", ".join(effects) + "."


def _tradeoff_summary(top: ScoredAction) -> str:
    """Disclose the tradeoff of pursuing the top action."""
    tradeoffs: list[str] = []

    if top.goal_delta > 0 and top.risk_delta < -0.01:
        tradeoffs.append("higher expected return comes with increased portfolio risk")
    if top.liquidity_delta < -0.1:
        tradeoffs.append("short-term cash reserves will decrease")
    if top.goal_delta < 0:
        tradeoffs.append("goal timeline may be impacted")

    if not tradeoffs:
        return "No significant tradeoffs identified for this action."

    return "Be aware: " + "; ".join(tradeoffs) + "."
