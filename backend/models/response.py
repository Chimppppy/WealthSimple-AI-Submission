from typing import Optional
from pydantic import BaseModel
from backend.models.financial_state import FinancialState
from backend.models.action import ScoredAction
from backend.models.market_data import MarketContext


class TopRecommendation(BaseModel):
    """The single highest-leverage action surfaced to the user."""

    action: str
    impact_summary: str
    tradeoff: str


class EvaluationMeta(BaseModel):
    """Metadata about the evaluation run."""

    engine_version: str
    scenario_count: int
    actions_evaluated: int
    data_source: str


class EvaluationResponse(BaseModel):
    """Top-level API response for POST /evaluate."""

    financial_snapshot: FinancialState
    ranked_actions: list[ScoredAction]
    top_recommendation: TopRecommendation
    meta: EvaluationMeta
    market_context: Optional[MarketContext] = None
