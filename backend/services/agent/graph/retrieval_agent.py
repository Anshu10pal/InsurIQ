"""Agent 1 — retrieval agent. Runs hybrid search and returns top-5 claims."""
from services.agent.graph.state import ClaimInvestigationState
from services.agent.guardrails.query_intent_detector import extract_metadata_filters, merge_with_user_filters
from services.rag.chroma_client import vector_search
from services.rag.fts_client import fts_search
from services.rag.rrf_merger import reciprocal_rank_fusion
from services.rag.score_reranker import rerank_by_score
from services.ingestion.embedder import generate_single_embedding
from config import settings
from utils.logging import get_logger

logger = get_logger(__name__)


def retrieval_agent(state: ClaimInvestigationState) -> ClaimInvestigationState:
    logger.info("retrieval_agent_started")
    state["current_agent"] = "retrieval"
    try:
        query = state.get("rewritten_query") or state.get("query", "")
        user_filters = state.get("filters") or {}
        detected_filters = extract_metadata_filters(query)
        merged_filters = merge_with_user_filters(detected_filters, user_filters)

        try:
            embed_query = query
            query_embedding = generate_single_embedding(embed_query)
            vector_results = vector_search(query_embedding, top_k=settings.rag_top_k_vector, filters=merged_filters)
        except Exception as e:
            logger.warning("vector_search_failed_falling_back", error=str(e))
            vector_results = []

        try:
            fts_results = fts_search(query, filters=merged_filters, top_k=settings.rag_top_k_fts)
        except Exception as e:
            logger.warning("fts_search_failed", error=str(e))
            fts_results = []

        if vector_results or fts_results:
            merged = reciprocal_rank_fusion(vector_results, fts_results)
            top_claims = rerank_by_score(merged, top_k=settings.rag_top_k_final)
        else:
            top_claims = []

        state["retrieved_claims"] = top_claims
        state["completed_agents"] = state.get("completed_agents", []) + ["retrieval"]
        logger.info("retrieval_agent_complete", claims_retrieved=len(top_claims))
    except Exception as e:
        logger.error("retrieval_agent_failed", error=str(e))
        state["retrieved_claims"] = []
        state["warning"] = f"Retrieval degraded: {str(e)}"
        state["partial_result"] = True
    return state
