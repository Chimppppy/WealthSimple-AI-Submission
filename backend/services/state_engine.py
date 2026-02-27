from backend.models.user_profile import UserProfile
from backend.models.financial_state import FinancialState, ScenarioResult

DEFAULT_EQUITY_RETURN = 0.06
DEFAULT_BOND_RETURN = 0.03
DEFAULT_CASH_RETURN = 0.01


def _build_scenarios(equity_ret: float, bond_ret: float) -> list[dict]:
    """Build scenario definitions scaled relative to the real base returns."""
    return [
        {"name": "base", "label": "Base Case", "equity": equity_ret, "bond": bond_ret},
        {
            "name": "recession",
            "label": "Recession",
            "equity_shock_y1": -0.20,
            "equity_recovery": max(equity_ret - 0.02, 0.01),
            "bond": max(bond_ret - 0.01, 0.005),
        },
        {"name": "bull", "label": "Bull Case", "equity": equity_ret + 0.04, "bond": bond_ret + 0.01},
    ]


def compute_financial_state(
    profile: UserProfile,
    equity_return: float | None = None,
    bond_return: float | None = None,
    cash_return: float | None = None,
) -> FinancialState:
    """Derive a full financial snapshot with multi-scenario projections and insights.

    When real market returns are provided they replace the default assumptions.
    """
    eq_ret = equity_return if equity_return is not None else DEFAULT_EQUITY_RETURN
    bd_ret = bond_return if bond_return is not None else DEFAULT_BOND_RETURN
    ca_ret = cash_return if cash_return is not None else DEFAULT_CASH_RETURN

    monthly_income = profile.annual_income / 12.0
    monthly_surplus = monthly_income - profile.monthly_expenses
    savings_rate = max(monthly_surplus / monthly_income, 0.0) if monthly_income > 0 else 0.0

    liquidity_ratio = (
        profile.cash_balance / profile.monthly_expenses
        if profile.monthly_expenses > 0
        else 0.0
    )

    cash_pct = max(1.0 - profile.portfolio_equity_pct - profile.portfolio_bond_pct, 0.0)
    base_return = (
        profile.portfolio_equity_pct * eq_ret
        + profile.portfolio_bond_pct * bd_ret
        + cash_pct * ca_ret
    )

    risk_exposure = _compute_risk_exposure(profile)
    scenarios = _run_scenarios(profile, eq_ret, bd_ret, ca_ret)
    base_scenario = scenarios[0]
    goal_gap = base_scenario.projected_value - profile.goal_target_amount
    insights = _generate_insights(profile, savings_rate, liquidity_ratio, risk_exposure, scenarios)

    return FinancialState(
        savings_rate=round(savings_rate, 4),
        monthly_surplus=round(monthly_surplus, 2),
        liquidity_ratio=round(liquidity_ratio, 2),
        projected_base_return=round(base_return, 4),
        risk_exposure_score=round(risk_exposure, 4),
        goal_funding_gap=round(goal_gap, 2),
        estimated_goal_probability=base_scenario.goal_probability,
        scenarios=scenarios,
        insights=insights,
    )


def project_future_value(
    portfolio_value: float,
    cash_balance: float,
    monthly_contribution: float,
    annual_return: float,
    years: int,
    cash_rate: float = DEFAULT_CASH_RETURN,
) -> float:
    """Compound growth projection separating portfolio and cash growth.

    Portfolio and contributions grow at the blended annual_return.
    Cash grows at cash_rate.
    """
    if annual_return == 0:
        portfolio_fv = portfolio_value + monthly_contribution * 12 * years
    else:
        g = (1 + annual_return) ** years
        portfolio_fv = portfolio_value * g + (
            monthly_contribution * 12 * ((g - 1) / annual_return)
        )

    cash_fv = cash_balance * (1 + cash_rate) ** years
    return portfolio_fv + cash_fv


def _run_scenarios(
    profile: UserProfile,
    equity_ret: float,
    bond_ret: float,
    cash_ret: float,
) -> list[ScenarioResult]:
    """Project future value and goal probability under base, recession, and bull scenarios."""
    scenarios = _build_scenarios(equity_ret, bond_ret)
    results: list[ScenarioResult] = []
    n = profile.goal_years

    for s in scenarios:
        if "equity_shock_y1" in s:
            annual_return = _recession_blended_return(profile, s, n, cash_ret)
        else:
            cash_pct = max(1.0 - profile.portfolio_equity_pct - profile.portfolio_bond_pct, 0.0)
            annual_return = (
                profile.portfolio_equity_pct * s["equity"]
                + profile.portfolio_bond_pct * s["bond"]
                + cash_pct * cash_ret
            )

        fv = project_future_value(
            profile.portfolio_value, profile.cash_balance,
            profile.monthly_contribution, annual_return, n, cash_ret,
        )
        goal_prob = min(fv / profile.goal_target_amount, 1.0) if profile.goal_target_amount > 0 else 1.0

        results.append(ScenarioResult(
            name=s["name"],
            label=s["label"],
            annual_return=round(annual_return, 4),
            projected_value=round(fv, 2),
            goal_probability=round(goal_prob, 4),
        ))
    return results


def _recession_blended_return(
    profile: UserProfile, scenario: dict, years: int, cash_ret: float = DEFAULT_CASH_RETURN
) -> float:
    """Compute effective annualized return for a recession scenario.

    Year 1: equity shock, then recovery rate for remaining years.
    Annualized = ((1+r1) * (1+r2)^(n-1))^(1/n) - 1
    """
    if years <= 0:
        return 0.0

    equity_y1 = 1 + scenario["equity_shock_y1"]
    equity_recovery = 1 + scenario["equity_recovery"]
    bond_rate = scenario["bond"]

    if years == 1:
        eq_annualized = scenario["equity_shock_y1"]
    else:
        eq_compound = equity_y1 * (equity_recovery ** (years - 1))
        eq_annualized = eq_compound ** (1.0 / years) - 1

    cash_pct = max(1.0 - profile.portfolio_equity_pct - profile.portfolio_bond_pct, 0.0)
    return (
        profile.portfolio_equity_pct * eq_annualized
        + profile.portfolio_bond_pct * bond_rate
        + cash_pct * cash_ret
    )


def _compute_risk_exposure(profile: UserProfile) -> float:
    """Risk score 0-1 combining equity weight and risk-tolerance mismatch."""
    tolerance_map = {"low": 0.30, "medium": 0.55, "high": 0.80}
    ideal_equity = tolerance_map.get(profile.risk_profile, 0.55)
    mismatch = max(profile.portfolio_equity_pct - ideal_equity, 0.0)
    return min(profile.portfolio_equity_pct * 0.7 + mismatch * 0.3, 1.0)


def _generate_insights(
    profile: UserProfile,
    savings_rate: float,
    liquidity_ratio: float,
    risk_exposure: float,
    scenarios: list[ScenarioResult],
) -> list[str]:
    """Generate plain-language insights based on the financial snapshot."""
    insights: list[str] = []

    if savings_rate >= 0.30:
        insights.append(f"Savings rate of {savings_rate:.0%} is excellent — well above the recommended 20%.")
    elif savings_rate >= 0.15:
        insights.append(f"Savings rate of {savings_rate:.0%} is solid. Aim for 20%+ to accelerate goals.")
    else:
        insights.append(f"Savings rate of {savings_rate:.0%} is below 15% — consider reducing discretionary spending.")

    if liquidity_ratio >= 6:
        insights.append(f"Emergency fund covers {liquidity_ratio:.1f} months — meets the 6-month safety target.")
    elif liquidity_ratio >= 3:
        insights.append(f"Emergency fund covers {liquidity_ratio:.1f} months — consider building to 6 months.")
    else:
        insights.append(f"Emergency fund covers only {liquidity_ratio:.1f} months — below the 3-month minimum. Priority action needed.")

    base = scenarios[0]
    recession = next((s for s in scenarios if s.name == "recession"), None)
    if recession and recession.goal_probability < base.goal_probability:
        drop = base.goal_probability - recession.goal_probability
        insights.append(
            f"Under recession conditions, goal probability drops by {drop:.0%} to {recession.goal_probability:.0%}."
        )

    if base.goal_probability >= 0.80:
        insights.append("You are on track to reach your financial goal under base conditions.")
    elif base.goal_probability >= 0.50:
        insights.append(f"Goal probability is {base.goal_probability:.0%} — achievable but action will improve odds.")
    else:
        insights.append(f"Goal probability is only {base.goal_probability:.0%} — significant adjustments recommended.")

    tolerance_map = {"low": 0.30, "medium": 0.55, "high": 0.80}
    ideal = tolerance_map.get(profile.risk_profile, 0.55)
    if profile.portfolio_equity_pct > ideal + 0.15:
        insights.append(
            f"Equity allocation of {profile.portfolio_equity_pct:.0%} significantly exceeds "
            f"your {profile.risk_profile}-risk target of {ideal:.0%}."
        )

    return insights
