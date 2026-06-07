"""Risk calculator — combines rule + statistical scores into 0-100 score."""
from typing import List, Dict, Any
from services.fraud.scoring.signal_definitions import SIGNAL_WEIGHTS
from services.fraud.scoring.statistical_scorer import compute_base_rate_component


def calculate_risk_score(rule_signals: List[str], statistical_flags: List[str], claim: Dict[str, Any]) -> int:
    rule_score = min(sum(SIGNAL_WEIGHTS.get(s, 5) for s in rule_signals), 60)
    stat_score = min(len(statistical_flags) * 10, 30)
    base_rate = compute_base_rate_component(claim)
    base_rate_score = min(round((base_rate / 0.10) * 10), 10)
    return max(0, min(100, rule_score + stat_score + base_rate_score))


def get_risk_level(score: int) -> str:
    if score >= 70: return "HIGH"
    elif score >= 40: return "MEDIUM"
    return "LOW"
