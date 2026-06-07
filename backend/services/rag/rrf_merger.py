"""Reciprocal Rank Fusion — merges vector and FTS result lists."""
from typing import List, Dict, Any


def reciprocal_rank_fusion(
    vector_results: List[Dict[str, Any]],
    fts_results: List[Dict[str, Any]],
    k: int = 60,
) -> List[Dict[str, Any]]:
    scores: Dict[int, float] = {}
    claim_map: Dict[int, Dict] = {}

    for rank, claim in enumerate(vector_results):
        pn = int(claim.get("policy_number", 0))
        scores[pn] = scores.get(pn, 0) + 1 / (k + rank + 1)
        claim_map[pn] = claim

    for rank, claim in enumerate(fts_results):
        pn = int(claim.get("policy_number", 0))
        scores[pn] = scores.get(pn, 0) + 1 / (k + rank + 1)
        if pn not in claim_map:
            claim_map[pn] = claim

    merged = []
    for pn, rrf_score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        claim = claim_map[pn].copy()
        claim["rrf_score"] = round(rrf_score, 6)
        merged.append(claim)

    return merged
