from pydantic import BaseModel, Field
from typing import Literal, Optional


class UserProfile(BaseModel):
    """Complete financial profile submitted by the user for evaluation."""

    annual_income: float = Field(..., gt=0, description="Gross annual income")
    monthly_expenses: float = Field(..., gt=0, description="Total monthly expenses")
    cash_balance: float = Field(..., ge=0, description="Liquid cash / savings balance")
    portfolio_value: float = Field(
        0.0, ge=0, description="Current total invested portfolio value"
    )
    portfolio_equity_pct: float = Field(
        ..., ge=0, le=1, description="Equity allocation as a fraction (0-1)"
    )
    portfolio_bond_pct: float = Field(
        ..., ge=0, le=1, description="Bond allocation as a fraction (0-1)"
    )
    monthly_contribution: float = Field(
        ..., ge=0, description="Monthly investment contribution"
    )
    goal_target_amount: float = Field(..., gt=0, description="Dollar target for the goal")
    goal_years: int = Field(..., gt=0, le=50, description="Years until the goal deadline")
    risk_profile: Literal["low", "medium", "high"] = Field(
        ..., description="Self-assessed risk tolerance"
    )

    first_name: Optional[str] = Field(
        None, max_length=50, description="User's first name for personalized AI output"
    )
    age: Optional[int] = Field(
        None, ge=16, le=100, description="User's age for life-stage context"
    )
    life_stage: Optional[str] = Field(
        None, description="Life stage: student, early_career, mid_career, pre_retirement, retired"
    )
    goal_purpose: Optional[str] = Field(
        None, description="What the user is saving for: home, retirement, education, travel, emergency, general_wealth"
    )
    financial_concern: Optional[str] = Field(
        None, description="Top financial concern: market_volatility, not_saving_enough, debt, inflation, retirement_readiness, none"
    )
    personal_note: Optional[str] = Field(
        None, max_length=300, description="Free-text note about the user's financial situation"
    )
