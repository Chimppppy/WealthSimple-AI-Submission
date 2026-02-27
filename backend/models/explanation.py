from typing import Optional
from pydantic import BaseModel
from backend.models.financial_state import FinancialState
from backend.models.action import ScoredAction
from backend.models.response import TopRecommendation


class ExplanationRequest(BaseModel):
    """Input to the LLM explanation layer — all data is pre-computed by the deterministic core."""

    risk_profile: str
    financial_snapshot: FinancialState
    ranked_actions: list[ScoredAction]
    top_recommendation: TopRecommendation

    first_name: Optional[str] = None
    age: Optional[int] = None
    life_stage: Optional[str] = None
    goal_purpose: Optional[str] = None
    financial_concern: Optional[str] = None
    personal_note: Optional[str] = None


class AIExplanation(BaseModel):
    """Structured output from the LLM explanation layer."""

    narrative: str
    reasoning: str
    alternatives_analysis: str
    risk_warnings: list[str]
    confidence_score: float
    disclaimer: str


class ExplanationResponse(BaseModel):
    """API response wrapper for the AI explanation."""

    explanation: AIExplanation
    model_used: str
    guardrails: list[str]
