"""Output guardrail — validates investigation response schema."""
from typing import Tuple, Dict, Any


def validate_investigation_response(response: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    required = ["risk_score", "risk_level", "fraud_signals", "retrieved_claims",
                "recommendation", "confidence", "action_steps"]
    cleaned = response.copy()
    for key in required:
        if key not in cleaned:
            if key == "risk_score": cleaned[key] = 0
            elif key == "risk_level": cleaned[key] = "LOW"
            elif key in ("fraud_signals", "retrieved_claims", "action_steps"): cleaned[key] = []
            elif key == "recommendation": cleaned[key] = "Investigation recommended."
            elif key == "confidence": cleaned[key] = 0.7

    score = cleaned.get("risk_score", 0)
    if not isinstance(score, (int, float)) or score < 0 or score > 100:
        cleaned["risk_score"] = max(0, min(100, int(score or 0)))

    level = cleaned.get("risk_level", "LOW")
    if level not in ("HIGH", "MEDIUM", "LOW", "UNKNOWN"):
        cleaned["risk_level"] = "LOW"

    return True, cleaned
