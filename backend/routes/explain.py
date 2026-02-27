from fastapi import APIRouter, HTTPException
from backend.models.explanation import ExplanationRequest, ExplanationResponse
from backend.services.llm_engine import (
    generate_explanation,
    get_model_name,
    GUARDRAILS,
)

router = APIRouter()


@router.post("/explain", response_model=ExplanationResponse)
async def explain(request: ExplanationRequest) -> ExplanationResponse:
    """Generate an AI explanation of pre-computed deterministic results.

    This endpoint does NOT perform any financial calculations.
    All numbers in the request were computed by the deterministic engine.
    The LLM interprets and explains them in plain language.
    """
    try:
        explanation = await generate_explanation(request)
    except EnvironmentError:
        raise HTTPException(
            status_code=503,
            detail="AI explanation unavailable: OPENAI_API_KEY not configured.",
        )
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="AI explanation failed. Deterministic results remain valid.",
        )

    return ExplanationResponse(
        explanation=explanation,
        model_used=get_model_name(),
        guardrails=list(GUARDRAILS),
    )
