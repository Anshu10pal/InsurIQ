"""LangGraph pipeline — assembles the 4-agent investigation graph."""
from langgraph.graph import StateGraph, END
from services.agent.graph.state import ClaimInvestigationState
from services.agent.graph.retrieval_agent import retrieval_agent
from services.agent.graph.fraud_agent import fraud_agent
from services.agent.graph.policy_agent import policy_agent
from services.agent.graph.recommendation_agent import recommendation_agent
from utils.logging import get_logger

logger = get_logger(__name__)

_graph = None


def _build_graph():
    graph = StateGraph(ClaimInvestigationState)
    graph.add_node("retrieval", retrieval_agent)
    graph.add_node("fraud_analysis", fraud_agent)
    graph.add_node("policy_validation", policy_agent)
    graph.add_node("recommendation", recommendation_agent)
    graph.set_entry_point("retrieval")
    graph.add_edge("retrieval", "fraud_analysis")
    graph.add_edge("fraud_analysis", "policy_validation")
    graph.add_edge("policy_validation", "recommendation")
    graph.add_edge("recommendation", END)
    return graph.compile()


def run_investigation(query: str, filters: dict = None, trace_id: str = None, use_query_rewriting: bool = False) -> dict:
    global _graph
    if _graph is None:
        _graph = _build_graph()

    initial_state = ClaimInvestigationState(
        query=query, filters=filters or {}, use_query_rewriting=use_query_rewriting,
        rewritten_query=None, retrieved_claims=[], fraud_signals=[], statistical_flags=[],
        fraud_score=0, risk_level="LOW", policy_issues=[], recommendation="",
        confidence=0.7, action_steps=[], cross_claim_patterns=[],
        trace_id=trace_id or "", completed_agents=[], current_agent="starting",
        partial_result=False, warning=None,
    )

    try:
        result = _graph.invoke(initial_state)
        return dict(result)
    except Exception as e:
        logger.error("pipeline_failed", error=str(e))
        return {**initial_state, "warning": str(e), "partial_result": True}
