from pydantic import BaseModel
from typing import Optional


class Action(BaseModel):
    """A candidate financial action the user could take."""

    name: str
    description: str
    equity_pct_delta: float = 0.0
    bond_pct_delta: float = 0.0
    contribution_delta_pct: float = 0.0
    cash_target_months: Optional[float] = None
    pause_contributions: bool = False
    goal_years_delta: int = 0


class ScoredAction(BaseModel):
    """An action after simulation and scoring."""

    name: str
    description: str
    goal_delta: float
    liquidity_delta: float
    risk_delta: float
    total_score: float
    rationale: str
