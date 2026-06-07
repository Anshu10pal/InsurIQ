"""LangGraph state definition for claim investigation pipeline."""
from typing import TypedDict, List, Optional


class ClaimInvestigationState(TypedDict):
    query: str
    filters: Optional[dict]
    use_query_rewriting: bool
    rewritten_query: Optional[str]
    retrieved_claims: List[dict]
    fraud_signals: List[str]
    statistical_flags: List[str]
    fraud_score: int
    risk_level: str
    policy_issues: List[str]
    recommendation: str
    confidence: float
    action_steps: List[str]
    cross_claim_patterns: List[str]
    trace_id: str
    completed_agents: List[str]
    current_agent: str
    partial_result: bool
    warning: Optional[str]
