from pydantic import BaseModel


class ScenarioResult(BaseModel):
    """Projection outcome under a single macro scenario."""

    name: str
    label: str
    annual_return: float
    projected_value: float
    goal_probability: float


class FinancialState(BaseModel):
    """Deterministic snapshot derived from a UserProfile, including scenario analysis."""

    savings_rate: float
    monthly_surplus: float
    liquidity_ratio: float
    projected_base_return: float
    risk_exposure_score: float
    goal_funding_gap: float
    estimated_goal_probability: float
    scenarios: list[ScenarioResult]
    insights: list[str]
