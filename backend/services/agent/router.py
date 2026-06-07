"""Agent service router - investigation endpoints."""
import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.claim import InvestigationRequest, FeedbackRequest, FeedbackLog
from services.agent.graph.pipeline import run_investigation
from services.agent.tools.cache_tool import get_cached_response, cache_response
from services.agent.guardrails.input_guard import validate_input, is_insurance_relevant
from services.agent.guardrails.output_guard import validate_investigation_response
from database import get_db
from utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/investigate")
async def investigate_claim(request: InvestigationRequest, db: Session = Depends(get_db)):
    is_valid, sanitized_query = validate_input(request.query)
    if not is_valid:
        raise HTTPException(status_code=400, detail=sanitized_query)

    trace_id = str(uuid.uuid4())
    filters = request.filters or {}

    cached = get_cached_response(sanitized_query, filters)
    if cached:
        cached["cache_hit"] = True
        cached["trace_id"] = trace_id
        return cached

    try:
        result = run_investigation(
            query=sanitized_query, filters=filters or None,
            trace_id=trace_id, use_query_rewriting=request.use_query_rewriting,
        )
        response = {
            "query": sanitized_query,
            "risk_score": result.get("fraud_score", 0),
            "fraud_score": result.get("fraud_score", 0),
            "risk_level": result.get("risk_level", "LOW"),
            "fraud_signals": result.get("fraud_signals", []),
            "statistical_flags": result.get("statistical_flags", []),
            "policy_issues": result.get("policy_issues", []),
            "retrieved_claims": result.get("retrieved_claims", []),
            "recommendation": result.get("recommendation", ""),
            "confidence": result.get("confidence", 0.7),
            "action_steps": result.get("action_steps", []),
            "trace_id": trace_id,
            "cache_hit": False,
            "rewritten_query": result.get("rewritten_query"),
            "partial_result": result.get("partial_result", False),
            "warning": result.get("warning"),
        }
        _, cleaned = validate_investigation_response(response)
        cache_response(sanitized_query, cleaned, filters)
        return cleaned
    except Exception as e:
        logger.error("investigation_failed", trace_id=trace_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Investigation failed: {str(e)}")


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    feedback = FeedbackLog(
        policy_number=request.policy_number, trace_id=request.trace_id,
        was_correct=request.was_correct, analyst_notes=request.analyst_notes,
    )
    db.add(feedback)
    db.commit()
    return {"status": "feedback_recorded", "trace_id": request.trace_id}


@router.get("/investigate/progress/{trace_id}")
async def get_progress(trace_id: str):
    return {"trace_id": trace_id, "status": "complete"}
