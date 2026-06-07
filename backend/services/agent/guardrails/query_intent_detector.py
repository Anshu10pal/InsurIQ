"""
Query Intent Detector — extracts explicit metadata filters from natural language queries.

Handles original fields:
    - police_report, witness, agent_type, accident_area, prior_claims, supplements, address_change, fault

Handles new engineered feature fields:
    - no_evidence (combined no_police + no_witness)
    - is_high_value_claim
    - is_new_policy
    - is_repeat_claimant
    - has_excess_supplements
    - is_weekend
    - recent_address_change
    - is_external_agent

Updated: renamed number_of_suppliments -> number_of_supplements
"""
import re
from typing import Dict, Any
from utils.logging import get_logger

logger = get_logger(__name__)

NEGATION_PREFIXES = [
    "no ", "without ", "missing ", "absent ", "lack of ",
    "not filed", "not present", "none", "didn't file",
    "did not file", "wasn't", "wasn't filed"
]


def _has_negation(text: str, keyword: str) -> bool:
    """Check if a keyword appears with a negation prefix nearby."""
    text_lower    = text.lower()
    keyword_lower = keyword.lower()
    idx = text_lower.find(keyword_lower)
    if idx == -1:
        return False
    prefix_window = text_lower[max(0, idx - 30):idx]
    for neg in NEGATION_PREFIXES:
        if neg in prefix_window:
            return True
    words_before = prefix_window.strip().split()
    if words_before and words_before[-1] in ["no", "not", "without", "none"]:
        return True
    return False


def extract_metadata_filters(query: str) -> Dict[str, Any]:
    """
    Extract explicit metadata filters from a natural language query.
    Returns dict of ChromaDB-compatible metadata filters.
    """
    query_lower = query.lower()
    filters     = {}

    # ── Police Report ───────────────────────────────────────────────────────────
    if any(kw in query_lower for kw in ["police report", "police filed", "filed police"]):
        if _has_negation(query_lower, "police report") or \
           _has_negation(query_lower, "police filed"):
            filters["police_report_filed"] = "No"
            logger.info("intent_detected", feature="police_report_filed", value="No")
        else:
            filters["police_report_filed"] = "Yes"
            logger.info("intent_detected", feature="police_report_filed", value="Yes")

    # ── Witness Present ─────────────────────────────────────────────────────────
    if any(kw in query_lower for kw in ["witness", "witnesses"]):
        if _has_negation(query_lower, "witness") or \
           _has_negation(query_lower, "witnesses") or \
           "no witness" in query_lower or \
           "no witnesses" in query_lower:
            filters["witness_present"] = "No"
            logger.info("intent_detected", feature="witness_present", value="No")
        else:
            filters["witness_present"] = "Yes"
            logger.info("intent_detected", feature="witness_present", value="Yes")

    # ── Agent Type ──────────────────────────────────────────────────────────────
    if "internal agent" in query_lower:
        filters["agent_type"]      = "Internal"
        filters["is_external_agent"] = 0
        logger.info("intent_detected", feature="agent_type", value="Internal")
    elif "external agent" in query_lower:
        filters["agent_type"]      = "External"
        filters["is_external_agent"] = 1
        logger.info("intent_detected", feature="agent_type", value="External")

    # ── Accident Area ───────────────────────────────────────────────────────────
    if "rural area" in query_lower or " rural " in query_lower:
        filters["accident_area"] = "Rural"
        logger.info("intent_detected", feature="accident_area", value="Rural")
    elif "urban area" in query_lower or " urban " in query_lower:
        filters["accident_area"] = "Urban"
        logger.info("intent_detected", feature="accident_area", value="Urban")

    # ── Prior Claims ────────────────────────────────────────────────────────────
    if any(kw in query_lower for kw in [
        "no prior claims", "no previous claims",
        "no claims history", "first claim"
    ]):
        filters["past_number_of_claims"] = "none"
        filters["is_repeat_claimant"]    = 0
        logger.info("intent_detected", feature="past_number_of_claims", value="none")
    elif any(kw in query_lower for kw in [
        "repeat claimant", "multiple prior claims",
        "prior claims", "previous claims", "claims history"
    ]):
        filters["is_repeat_claimant"] = 1
        logger.info("intent_detected", feature="is_repeat_claimant", value=1)

    # ── Supplements ─────────────────────────────────────────────────────────────
    if any(kw in query_lower for kw in [
        "no supplements", "no repair supplements",
        "minimal supplements", "zero supplements"
    ]):
        filters["number_of_supplements"]  = "none"   # renamed
        filters["has_excess_supplements"] = 0
        logger.info("intent_detected", feature="number_of_supplements", value="none")
    elif any(kw in query_lower for kw in [
        "excess supplements", "inflated repair", "high supplements",
        "many supplements", "repair inflation"
    ]):
        filters["has_excess_supplements"] = 1
        logger.info("intent_detected", feature="has_excess_supplements", value=1)

    # ── Address Change ──────────────────────────────────────────────────────────
    if any(kw in query_lower for kw in [
        "no address change", "same address", "no address changes"
    ]):
        filters["address_change_claim"]  = "no change"
        filters["recent_address_change"] = 0
        logger.info("intent_detected", feature="address_change_claim", value="no change")
    elif any(kw in query_lower for kw in [
        "address change", "changed address", "recent address"
    ]):
        filters["recent_address_change"] = 1
        logger.info("intent_detected", feature="recent_address_change", value=1)

    # ── Fault ───────────────────────────────────────────────────────────────────
    if "policyholder at fault" in query_lower or \
       "policy holder at fault" in query_lower or \
       "claimant at fault" in query_lower:
        filters["fault"] = "Policy Holder"
        logger.info("intent_detected", feature="fault", value="Policy Holder")
    elif "third party at fault" in query_lower or \
         "third party fault" in query_lower:
        filters["fault"] = "Third Party"
        logger.info("intent_detected", feature="fault", value="Third Party")

    # ── NEW: No Evidence (combined no police + no witness) ──────────────────────
    if any(kw in query_lower for kw in [
        "no evidence", "no proof", "no documentation",
        "unwitnessed and unreported", "no police and no witness"
    ]):
        filters["no_evidence"] = 1
        logger.info("intent_detected", feature="no_evidence", value=1)

    # ── NEW: High Value Claim ────────────────────────────────────────────────────
    if any(kw in query_lower for kw in [
        "high value", "expensive vehicle", "luxury vehicle",
        "high price", "high vehicle price", "more than 69000",
        "high amount", "large claim"
    ]):
        filters["is_high_value_claim"] = 1
        logger.info("intent_detected", feature="is_high_value_claim", value=1)

    # ── NEW: New Policy ──────────────────────────────────────────────────────────
    if any(kw in query_lower for kw in [
        "new policy", "recent policy", "within a week",
        "week of inception", "new insurance", "policy gaming",
        "just started policy", "short policy duration"
    ]):
        filters["is_new_policy"] = 1
        logger.info("intent_detected", feature="is_new_policy", value=1)

    # ── NEW: Weekend Accident ────────────────────────────────────────────────────
    if any(kw in query_lower for kw in [
        "weekend accident", "saturday accident", "sunday accident",
        "weekend claims", "weekend collision"
    ]):
        filters["is_weekend"] = 1
        logger.info("intent_detected", feature="is_weekend", value=1)

    # ── Derived: No Evidence auto-set if both police and witness are No ──────────
    if filters.get("police_report_filed") == "No" and \
       filters.get("witness_present") == "No":
        filters["no_evidence"] = 1
        logger.info("intent_detected", feature="no_evidence", value=1, source="derived")

    logger.info(
        "intent_extraction_complete",
        query_preview=query[:60],
        filters_extracted=len(filters),
        filters=filters,
    )

    return filters


def merge_with_user_filters(
    detected_filters: Dict[str, Any],
    user_filters: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Merge auto-detected filters with user-provided filters.
    User filters take precedence over auto-detected ones.
    """
    merged = {**detected_filters}
    if user_filters:
        merged.update(user_filters)
    return merged if merged else None
