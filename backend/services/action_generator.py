from backend.models.user_profile import UserProfile
from backend.models.financial_state import FinancialState
from backend.models.action import Action

RISK_EQUITY_TARGET = {"low": 0.30, "medium": 0.55, "high": 0.80}


def generate_candidate_actions(
    profile: UserProfile, state: FinancialState
) -> list[Action]:
    """Dynamically generate 5-7 context-aware candidate actions based on the user's state."""
    actions: list[Action] = []

    actions.append(Action(
        name="Increase monthly contribution by 10%",
        description="Boost monthly investment contributions by 10% to accelerate goal progress.",
        contribution_delta_pct=0.10,
    ))

    ideal_equity = RISK_EQUITY_TARGET.get(profile.risk_profile, 0.55)
    if profile.portfolio_equity_pct < ideal_equity:
        gap = min(round(ideal_equity - profile.portfolio_equity_pct, 2), 0.15)
        actions.append(Action(
            name=f"Increase equity allocation by {gap:.0%}",
            description=f"Shift {gap:.0%} into equities to align with your {profile.risk_profile}-risk target of {ideal_equity:.0%}.",
            equity_pct_delta=gap,
        ))
    elif profile.portfolio_equity_pct > ideal_equity + 0.10:
        reduction = min(round(profile.portfolio_equity_pct - ideal_equity, 2), 0.15)
        actions.append(Action(
            name=f"Reduce equity allocation by {reduction:.0%}",
            description=f"De-risk by shifting {reduction:.0%} out of equities toward your {profile.risk_profile}-risk target.",
            equity_pct_delta=-reduction,
        ))
    else:
        actions.append(Action(
            name="Increase equity allocation by 10%",
            description="Shift 10 percentage points into equities for higher expected return.",
            equity_pct_delta=0.10,
        ))

    if state.liquidity_ratio < 3:
        actions.append(Action(
            name="Build emergency fund to 3 months",
            description="Priority: build cash reserves to cover at least 3 months of expenses.",
            cash_target_months=3.0,
        ))
    elif state.liquidity_ratio < 6:
        actions.append(Action(
            name="Increase emergency fund to 6 months",
            description="Build cash reserves to cover 6 months of expenses for full safety.",
            cash_target_months=6.0,
        ))
    else:
        actions.append(Action(
            name="Maintain emergency fund",
            description="Emergency fund is healthy. Consider deploying excess cash into investments.",
            cash_target_months=6.0,
        ))

    actions.append(Action(
        name="Increase bond allocation by 10%",
        description="Shift 10 percentage points into bonds for lower volatility and steadier income.",
        bond_pct_delta=0.10,
    ))

    if profile.monthly_contribution > 0:
        actions.append(Action(
            name="Pause contributions temporarily",
            description="Halt monthly contributions to free up cash flow in the short term.",
            pause_contributions=True,
        ))

    if state.estimated_goal_probability < 0.60 and profile.goal_years < 30:
        actions.append(Action(
            name="Extend goal timeline by 2 years",
            description="Adding 2 years gives compounding more time to work and significantly improves success probability.",
            goal_years_delta=2,
        ))

    if state.savings_rate < 0.15 and profile.monthly_contribution > 0:
        reduced = round(profile.monthly_contribution * 0.5, 2)
        actions.append(Action(
            name="Reduce contributions by 50%",
            description=f"Cut contributions to ${reduced:,.0f}/mo to rebuild cash reserves while still investing.",
            contribution_delta_pct=-0.50,
        ))

    return actions
