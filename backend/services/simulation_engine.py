from backend.models.user_profile import UserProfile
from backend.models.action import Action
from backend.services.state_engine import compute_financial_state


def simulate_action(
    profile: UserProfile, action: Action
) -> dict[str, float]:
    """Simulate the effect of applying *action* to *profile* over the projection horizon.

    Returns deltas for goal probability, liquidity ratio, and risk exposure.
    """
    baseline = compute_financial_state(profile)
    adjusted = _apply_action(profile, action)
    projected = compute_financial_state(adjusted)

    goal_delta = projected.estimated_goal_probability - baseline.estimated_goal_probability
    liquidity_delta = projected.liquidity_ratio - baseline.liquidity_ratio
    risk_delta = baseline.risk_exposure_score - projected.risk_exposure_score

    return {
        "goal_delta": round(goal_delta, 4),
        "liquidity_delta": round(liquidity_delta, 4),
        "risk_delta": round(risk_delta, 4),
    }


def _apply_action(profile: UserProfile, action: Action) -> UserProfile:
    """Return a modified copy of *profile* reflecting the action's adjustments."""
    new_equity = min(max(profile.portfolio_equity_pct + action.equity_pct_delta, 0.0), 1.0)
    new_bond = min(max(profile.portfolio_bond_pct + action.bond_pct_delta, 0.0), 1.0)

    total_alloc = new_equity + new_bond
    if total_alloc > 1.0:
        new_bond = 1.0 - new_equity

    new_contribution = profile.monthly_contribution
    if action.pause_contributions:
        new_contribution = 0.0
    elif action.contribution_delta_pct != 0.0:
        new_contribution = profile.monthly_contribution * (1.0 + action.contribution_delta_pct)

    new_cash = profile.cash_balance
    if action.cash_target_months is not None:
        target_cash = action.cash_target_months * profile.monthly_expenses
        if target_cash > profile.cash_balance:
            new_cash = target_cash

    new_years = max(profile.goal_years + action.goal_years_delta, 1)

    return profile.model_copy(
        update={
            "portfolio_equity_pct": round(new_equity, 4),
            "portfolio_bond_pct": round(new_bond, 4),
            "monthly_contribution": round(new_contribution, 2),
            "cash_balance": round(new_cash, 2),
            "goal_years": new_years,
        }
    )
