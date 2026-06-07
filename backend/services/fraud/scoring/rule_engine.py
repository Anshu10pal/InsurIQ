"""
Rule engine — evaluates 15 domain-specific fraud detection rules.
Each rule is deterministic, named, and independently testable.
Rules derived from EDA findings and insurance domain knowledge.

Updated: renamed NumberOfSuppliments -> NumberOfSupplements in all get() calls
         Logic and rules are unchanged.
"""
from typing import List, Dict, Any
from services.fraud.scoring.signal_definitions import (
    HIGH_AMOUNT_NO_POLICE,
    NEW_POLICY_QUICK_CLAIM,
    HIGH_PRIOR_CLAIMS,
    MULTIPLE_ADDRESS_CHANGES,
    EXTERNAL_AGENT_HIGH_CLAIM,
    NO_WITNESS_MULTI_CAR,
    EXCESS_SUPPLEMENTS,
    POLICY_HOLDER_AT_FAULT,
    WEEKEND_NO_WITNESS,
    NEW_POLICY_SHORT_DURATION,
    OLD_VEHICLE_HIGH_PRICE,
    RAPID_CLAIM_FILING,
    HIGH_DRIVER_RATING,
    URBAN_NO_EVIDENCE,
    REPEATED_CLAIM_PATTERN,
)
from services.ingestion.ordinal_maps import encode_ordinal


def evaluate_rules(claim: Dict[str, Any]) -> List[str]:
    """
    Evaluate all 15 fraud detection rules against a claim record.

    Args:
        claim: Dictionary of claim fields (raw CSV or DB record)

    Returns:
        List of triggered signal names (empty if no signals fired)
    """
    signals = []

    def get(field: str, snake: str = None, default=None):
        val = claim.get(field) or claim.get(snake or field.lower(), default)
        return val

    deductible    = float(get("Deductible",    "deductible")    or 0)
    driver_rating = int(get("DriverRating",    "driver_rating") or 0)

    past_claims_raw = str(get("PastNumberOfClaims", "past_number_of_claims") or "none")
    past_claims_num = encode_ordinal("PastNumberOfClaims", past_claims_raw)

    # Support both old spelling (suppliments) and new (supplements)
    supplements_raw = str(
        get("NumberOfSupplements", "number_of_supplements") or
        get("NumberOfSuppliments", "number_of_suppliments") or
        "none"
    )
    supplements_num = encode_ordinal("NumberOfSuppliments", supplements_raw)

    address_change_raw = str(get("AddressChange_Claim", "address_change_claim") or "no change")
    address_change_num = encode_ordinal("AddressChange_Claim", address_change_raw)

    days_accident_raw = str(get("Days_Policy_Accident", "days_policy_accident") or "more than 30")
    days_accident_num = encode_ordinal("Days_Policy_Accident", days_accident_raw)

    days_claim_raw = str(get("Days_Policy_Claim", "days_policy_claim") or "more than 30")
    days_claim_num = encode_ordinal("Days_Policy_Claim", days_claim_raw)

    age_vehicle_raw = str(get("AgeOfVehicle", "age_of_vehicle") or "new")
    age_vehicle_num = encode_ordinal("AgeOfVehicle", age_vehicle_raw)

    vehicle_price_raw = str(get("VehiclePrice", "vehicle_price") or "less than 20000")
    vehicle_price_num = encode_ordinal("VehiclePrice", vehicle_price_raw)

    num_cars_raw = str(get("NumberOfCars", "number_of_cars") or "1 vehicle")
    num_cars_num = encode_ordinal("NumberOfCars", num_cars_raw)

    police_report = str(get("PoliceReportFiled", "police_report_filed") or "No")
    witness       = str(get("WitnessPresent",    "witness_present")     or "No")
    agent_type    = str(get("AgentType",         "agent_type")          or "Internal")
    fault         = str(get("Fault",             "fault")               or "")
    accident_area = str(get("AccidentArea",      "accident_area")       or "")
    day_of_week   = str(get("DayOfWeek",         "day_of_week")         or "")

    # ── Rule 1: High amount claim with no police report ─────────────────────────
    if police_report.strip().lower() == "no" and vehicle_price_num >= 40000:
        signals.append(HIGH_AMOUNT_NO_POLICE)

    # ── Rule 2: Claim filed very quickly after accident ─────────────────────────
    if days_claim_num <= 4:
        signals.append(RAPID_CLAIM_FILING)

    # ── Rule 3: New policy, quick claim ─────────────────────────────────────────
    if days_accident_num <= 4:
        signals.append(NEW_POLICY_QUICK_CLAIM)

    # ── Rule 4: Short policy duration at accident time ──────────────────────────
    if days_accident_num <= 11:
        signals.append(NEW_POLICY_SHORT_DURATION)

    # ── Rule 5: High number of prior claims ─────────────────────────────────────
    if past_claims_num >= 3:
        signals.append(HIGH_PRIOR_CLAIMS)

    # ── Rule 6: Multiple address changes ────────────────────────────────────────
    if address_change_num >= 1:
        signals.append(MULTIPLE_ADDRESS_CHANGES)

    # ── Rule 7: External agent + high value claim ────────────────────────────────
    if agent_type.strip().lower() == "external" and vehicle_price_num >= 40000:
        signals.append(EXTERNAL_AGENT_HIGH_CLAIM)

    # ── Rule 8: Multi-car accident with no witnesses ────────────────────────────
    if num_cars_num >= 2 and witness.strip().lower() == "no":
        signals.append(NO_WITNESS_MULTI_CAR)

    # ── Rule 9: Excess repair supplements ───────────────────────────────────────
    if supplements_num >= 4:
        signals.append(EXCESS_SUPPLEMENTS)

    # ── Rule 10: Policy holder at fault ─────────────────────────────────────────
    if "policy holder" in fault.strip().lower():
        signals.append(POLICY_HOLDER_AT_FAULT)

    # ── Rule 11: Weekend accident with no witnesses ──────────────────────────────
    if day_of_week.strip().lower() in ["saturday", "sunday"] and \
       witness.strip().lower() == "no":
        signals.append(WEEKEND_NO_WITNESS)

    # ── Rule 12: Old vehicle with high repair cost ───────────────────────────────
    if age_vehicle_num >= 7 and vehicle_price_num >= 40000:
        signals.append(OLD_VEHICLE_HIGH_PRICE)

    # ── Rule 13: Worst driver rating ─────────────────────────────────────────────
    if driver_rating == 4:
        signals.append(HIGH_DRIVER_RATING)

    # ── Rule 14: Urban area — no police AND no witnesses ────────────────────────
    if accident_area.strip().lower() == "urban" and \
       police_report.strip().lower() == "no" and \
       witness.strip().lower() == "no":
        signals.append(URBAN_NO_EVIDENCE)

    # ── Rule 15: Repeated claim pattern ─────────────────────────────────────────
    if past_claims_num >= 3 and days_accident_num <= 22:
        signals.append(REPEATED_CLAIM_PATTERN)

    # Remove duplicates while preserving order
    seen = set()
    unique_signals = []
    for s in signals:
        if s not in seen:
            seen.add(s)
            unique_signals.append(s)
    return unique_signals
