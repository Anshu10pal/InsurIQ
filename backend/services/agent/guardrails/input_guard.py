"""Input guardrail — validates and sanitizes investigation queries."""
import re
from typing import Tuple
from config import settings

INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all)\s+instructions",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(if\s+you\s+are|a)",
    r"jailbreak",
    r"system\s*:\s*you",
    r"<\s*system\s*>",
]


def validate_input(query: str) -> Tuple[bool, str]:
    if not query or not query.strip():
        return False, "Query cannot be empty"
    q = query.strip()
    if len(q) < settings.min_query_length:
        return False, f"Query too short (minimum {settings.min_query_length} characters)"
    if len(q) > settings.max_query_length:
        return False, f"Query too long (maximum {settings.max_query_length} characters)"
    q_lower = q.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, q_lower):
            return False, "Query contains potentially harmful content"
    sanitized = re.sub(r'[<>"\']', '', q)
    return True, sanitized


def is_insurance_relevant(query: str) -> bool:
    insurance_keywords = [
        "claim", "fraud", "policy", "vehicle", "accident", "insurance",
        "agent", "repair", "supplement", "witness", "police", "collision",
        "liability", "deductible", "claimant", "suspicious", "investigate",
    ]
    q_lower = query.lower()
    return any(kw in q_lower for kw in insurance_keywords)
