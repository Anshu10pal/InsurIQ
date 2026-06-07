"""Score reranker — combines RRF score with pre-computed fraud score."""
from typing import List, Dict, Any


def rerank_by_score(claims: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    for claim in claims:
        rrf = float(claim.get("rrf_score", 0))
        fraud_score = float(claim.get("fraud_risk_score", 0)) / 100.0
        claim["final_relevance_score"] = round(0.8 * rrf / 0.02 + 0.2 * fraud_score, 4)
        claim["final_relevance_score"] = min(1.0, claim["final_relevance_score"])
    return sorted(claims, key=lambda x: x["final_relevance_score"], reverse=True)[:top_k]
