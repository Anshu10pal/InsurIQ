"""
PostgreSQL full-text search client.
Exports fts_search() as a standalone function for use by retrieval_agent.
Fixes:
  - NoneType: filters=None handled via safe_filters = filters or {}
  - SQL WHERE includes: police_report_filed, agent_type, witness_present,
    past_number_of_claims
  - Fallback chain: ts_vector -> ILIKE
"""
import logging
from sqlalchemy import text
from database import SessionLocal

logger = logging.getLogger(__name__)


def fts_search(query: str, filters: dict = None, top_k: int = 10) -> list[dict]:
    """
    Standalone function called by retrieval_agent.
    Opens its own DB session, runs hybrid FTS, closes session.
    """
    safe_filters = filters or {}
    db = SessionLocal()
    try:
        results = _ts_vector_search(db, query, safe_filters, top_k)
        if not results:
            logger.info("fts_ts_vector_empty — falling back to ILIKE")
            results = _ilike_search(db, query, safe_filters, top_k)
        return results
    finally:
        db.close()


def _build_where_clauses(safe_filters: dict) -> tuple[str, dict]:
    """Return (extra_sql, params) for optional filter columns."""
    clauses = []
    params: dict = {}

    if safe_filters.get("police_report_filed") is not None:
        clauses.append("police_report_filed = :police_report_filed")
        params["police_report_filed"] = safe_filters["police_report_filed"]

    if safe_filters.get("agent_type"):
        clauses.append("agent_type = :agent_type")
        params["agent_type"] = safe_filters["agent_type"]

    if safe_filters.get("witness_present") is not None:
        clauses.append("witness_present = :witness_present")
        params["witness_present"] = safe_filters["witness_present"]

    if safe_filters.get("past_number_of_claims") is not None:
        clauses.append("past_number_of_claims >= :past_number_of_claims")
        params["past_number_of_claims"] = safe_filters["past_number_of_claims"]

    extra_sql = (" AND " + " AND ".join(clauses)) if clauses else ""
    return extra_sql, params


def _ts_vector_search(db, query: str, safe_filters: dict, top_k: int) -> list[dict]:
    extra_sql, params = _build_where_clauses(safe_filters)
    params.update({"query": query, "top_k": top_k})
    try:
        sql = text(
            f"""
            SELECT id, policy_number, narrative, fraud_risk_score, fraud_found_p,
                   ts_rank(search_vector, plainto_tsquery('english', :query)) AS rank
            FROM claims
            WHERE search_vector @@ plainto_tsquery('english', :query)
            {extra_sql}
            ORDER BY rank DESC
            LIMIT :top_k
            """
        )
        rows = db.execute(sql, params).fetchall()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        logger.error(f"fts_ts_vector_error: {e}")
        return []


def _ilike_search(db, query: str, safe_filters: dict, top_k: int) -> list[dict]:
    extra_sql, params = _build_where_clauses(safe_filters)
    params.update({"query": f"%{query}%", "top_k": top_k})
    try:
        sql = text(
            f"""
            SELECT id, policy_number, narrative, fraud_risk_score, fraud_found_p,
                   0.5 AS rank
            FROM claims
            WHERE narrative ILIKE :query
            {extra_sql}
            ORDER BY fraud_risk_score DESC
            LIMIT :top_k
            """
        )
        rows = db.execute(sql, params).fetchall()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        logger.error(f"fts_ilike_error: {e}")
        return []


def _row_to_dict(row) -> dict:
    return {
        "id":               row.id,
        "policy_number":    row.policy_number,
        "narrative":        row.narrative,
        "fraud_risk_score": row.fraud_risk_score,
        "fraud_found_p":    row.fraud_found_p,
        "fts_rank":         float(row.rank),
    }