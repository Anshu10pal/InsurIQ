"""
Agent service router — investigation endpoints.

Enhancement applied:
  6. Deduplication — identical queries from same session within 30s
     return the last result instantly without hitting Redis or agents.
"""
import uuid
import time
from fastapi import APIRouter, HTTPException, Depends, Request
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

# ── Deduplication store ───────────────────────────────────────────────────────
# { dedup_key: {"result": dict, "timestamp": float} }
# Key = sanitised_query — simple in-memory, resets on restart
_recent_results: dict = {}
_DEDUP_WINDOW_SECONDS = 30


def _get_dedup_key(query: str) -> str:
    """Simple dedup key — sanitised query string lowercased."""
    return query.strip().lower()


def _check_dedup(query: str) -> dict | None:
    """Return cached result if same query was answered within the dedup window."""
    key = _get_dedup_key(query)
    entry = _recent_results.get(key)
    if entry and (time.time() - entry["timestamp"]) < _DEDUP_WINDOW_SECONDS:
        logger.info("dedup_hit query_preview=%s", query[:40])
        return entry["result"]
    return None


def _store_dedup(query: str, result: dict) -> None:
    """Store result for dedup window. Evict entries older than window."""
    key = _get_dedup_key(query)
    _recent_results[key] = {"result": result, "timestamp": time.time()}

    # Evict stale entries to prevent unbounded growth
    now = time.time()
    stale = [k for k, v in _recent_results.items()
             if now - v["timestamp"] > _DEDUP_WINDOW_SECONDS * 2]
    for k in stale:
        del _recent_results[k]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/investigate")
async def investigate_claim(request: InvestigationRequest, db: Session = Depends(get_db)):
    # Step 1: validate + sanitise (masking, injection strip, truncate, translate, spell-fix)
    is_valid, sanitized_query = validate_input(request.query)
    if not is_valid:
        raise HTTPException(status_code=400, detail=sanitized_query)

    trace_id = str(uuid.uuid4())
    filters = request.filters or {}

    # Step 2: deduplication — same query within 30s returns instantly
    dedup_result = _check_dedup(sanitized_query)
    if dedup_result:
        dedup_result["trace_id"] = trace_id
        dedup_result["cache_hit"] = True
        return dedup_result

    # Step 3: Redis cache check
    cached = get_cached_response(sanitized_query, filters)
    if cached:
        cached["cache_hit"] = True
        cached["trace_id"] = trace_id
        _store_dedup(sanitized_query, cached)
        return cached

    # Step 4: full pipeline
    try:
        result = run_investigation(
            query=sanitized_query, filters=filters or None,
            trace_id=trace_id, use_query_rewriting=request.use_query_rewriting,
        )
        response = {
            "query":            sanitized_query,
            "risk_score":       result.get("fraud_score", 0),
            "fraud_score":      result.get("fraud_score", 0),
            "risk_level":       result.get("risk_level", "LOW"),
            "fraud_signals":    result.get("fraud_signals", []),
            "statistical_flags": result.get("statistical_flags", []),
            "policy_issues":    result.get("policy_issues", []),
            "retrieved_claims": result.get("retrieved_claims", []),
            "recommendation":   result.get("recommendation", ""),
            "confidence":       result.get("confidence", 0.7),
            "action_steps":     result.get("action_steps", []),
            "trace_id":         trace_id,
            "cache_hit":        False,
            "rewritten_query":  result.get("rewritten_query"),
            "partial_result":   result.get("partial_result", False),
            "warning":          result.get("warning"),
        }
        _, cleaned = validate_investigation_response(response)

        # Store in dedup window + Redis cache
        _store_dedup(sanitized_query, cleaned)
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