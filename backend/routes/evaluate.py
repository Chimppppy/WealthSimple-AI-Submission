from fastapi import APIRouter
from backend.models.user_profile import UserProfile
from backend.models.response import EvaluationResponse, EvaluationMeta
from backend.services.state_engine import compute_financial_state
from backend.services.ranking_engine import rank_actions
from backend.services.market_data import get_market_context

router = APIRouter()


@router.post("/evaluate", response_model=EvaluationResponse)
def evaluate(profile: UserProfile) -> EvaluationResponse:
    """Accept a user financial profile, run deterministic analysis, and return ranked actions.

    Fetches real market data from Yahoo Finance to power projections.
    Falls back to hardcoded assumptions if market data is unavailable.
    """
    market = get_market_context(profile.portfolio_equity_pct, profile.portfolio_bond_pct)

    snapshot = compute_financial_state(
        profile,
        equity_return=market.equity_return,
        bond_return=market.bond_return,
        cash_return=market.cash_return,
    )
    ranked, top = rank_actions(profile, snapshot)

    return EvaluationResponse(
        financial_snapshot=snapshot,
        ranked_actions=ranked,
        top_recommendation=top,
        market_context=market,
        meta=EvaluationMeta(
            engine_version="0.3.0",
            scenario_count=len(snapshot.scenarios),
            actions_evaluated=len(ranked),
            data_source=market.data_source,
        ),
    )
