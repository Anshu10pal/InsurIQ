"""
Narrative builder — converts structured claim row into rich natural language.
Enriched version includes:
  - Fraud outcome emphasized at the start
  - Interpretive language explaining why features matter
  - Fraud signal names included directly in narrative
  - Engineered feature vocabulary for better semantic matching
  - Dataset-compatible vocabulary throughout

Updated: renamed NumberOfSuppliments -> NumberOfSupplements
         Added engineered feature summary section

Average output: ~250-300 tokens per claim (within 500 token limit)
"""
from typing import List


def build_claim_narrative(row: dict) -> str:
    """
    Build an enriched natural language narrative from a claim record.
    Includes engineered feature vocabulary so ChromaDB can match on
    combined risk signals like NO_EVIDENCE_PATTERN, HIGH_VALUE_CLAIM etc.

    Args:
        row: Dictionary of claim fields (from CSV or database)

    Returns:
        Enriched natural language narrative string (~270 tokens)
    """
    policy_num    = row.get("PolicyNumber",         row.get("policy_number",         "Unknown"))
    accident_area = row.get("AccidentArea",          row.get("accident_area",          "Unknown"))
    day           = row.get("DayOfWeek",             row.get("day_of_week",            "Unknown"))
    month         = row.get("Month",                 row.get("month",                  "Unknown"))
    year          = row.get("Year",                  row.get("year",                   "Unknown"))
    make          = row.get("Make",                  row.get("make",                   "Unknown"))
    vehicle_cat   = row.get("VehicleCategory",       row.get("vehicle_category",       "Unknown"))
    vehicle_price = row.get("VehiclePrice",          row.get("vehicle_price",          "Unknown"))
    age_vehicle   = row.get("AgeOfVehicle",          row.get("age_of_vehicle",         "Unknown"))
    age_holder    = row.get("AgeOfPolicyHolder",     row.get("age_of_policy_holder",   "Unknown"))
    sex           = row.get("Sex",                   row.get("sex",                    "Unknown"))
    marital       = row.get("MaritalStatus",         row.get("marital_status",         "Unknown"))
    fault         = row.get("Fault",                 row.get("fault",                  "Unknown"))
    base_policy   = row.get("BasePolicy",            row.get("base_policy",            "Unknown"))
    deductible    = row.get("Deductible",            row.get("deductible",             0))
    driver_rating = row.get("DriverRating",          row.get("driver_rating",          0))
    days_accident = row.get("Days_Policy_Accident",  row.get("days_policy_accident",   "Unknown"))
    days_claim    = row.get("Days_Policy_Claim",     row.get("days_policy_claim",      "Unknown"))
    past_claims   = row.get("PastNumberOfClaims",    row.get("past_number_of_claims",  "none"))
    police_report = row.get("PoliceReportFiled",     row.get("police_report_filed",    "Unknown"))
    witness       = row.get("WitnessPresent",        row.get("witness_present",        "Unknown"))
    agent_type    = row.get("AgentType",             row.get("agent_type",             "Unknown"))
    address_change = row.get("AddressChange_Claim",  row.get("address_change_claim",   "no change"))
    num_cars      = row.get("NumberOfCars",          row.get("number_of_cars",         "1 vehicle"))
    fraud_label   = int(row.get("FraudFound_P",      row.get("fraud_found_p",          0)))

    # Support both old (suppliments) and new (supplements) spelling
    supplements = (
        row.get("NumberOfSupplements") or
        row.get("number_of_supplements") or
        row.get("NumberOfSuppliments") or
        row.get("number_of_suppliments") or
        "none"
    )

    # Pre-computed signals if available
    fraud_signals = row.get("fraud_signals", []) or []
    if isinstance(fraud_signals, str):
        import json
        try:
            fraud_signals = json.loads(fraud_signals)
        except Exception:
            fraud_signals = []

    # ── Engineered features (from cleaned CSV) ──────────────────────────────────
    is_weekend             = int(row.get("IsWeekend",            row.get("is_weekend",             0)) or 0)
    no_evidence            = int(row.get("NoEvidence",           row.get("no_evidence",            0)) or 0)
    is_high_value_claim    = int(row.get("IsHighValueClaim",     row.get("is_high_value_claim",    0)) or 0)
    is_new_policy          = int(row.get("IsNewPolicy",          row.get("is_new_policy",          0)) or 0)
    is_repeat_claimant     = int(row.get("IsRepeatClaimant",     row.get("is_repeat_claimant",     0)) or 0)
    has_excess_supplements = int(row.get("HasExcessSupplements", row.get("has_excess_supplements", 0)) or 0)
    is_old_high_vehicle    = int(row.get("IsOldHighValueVehicle",row.get("is_old_high_vehicle",    0)) or 0)
    recent_address_change  = int(row.get("RecentAddressChange",  row.get("recent_address_change",  0)) or 0)
    is_external_agent      = int(row.get("IsExternalAgent",      row.get("is_external_agent",      0)) or 0)
    fraud_risk_flags       = int(row.get("FraudRiskFlags",       row.get("fraud_risk_flags",       0)) or 0)

    # ── Outcome header ──────────────────────────────────────────────────────────
    if fraud_label == 1:
        outcome_header = "FRAUD CONFIRMED CASE"
        outcome_text   = "This claim was investigated and confirmed as fraudulent."
    else:
        outcome_header = "LEGITIMATE CLAIM"
        outcome_text   = "This claim was processed as legitimate with no fraud confirmed."

    # ── Evidence interpretation ─────────────────────────────────────────────────
    evidence_parts = []

    if str(police_report).strip().lower() == "no":
        evidence_parts.append(
            "No police report was filed — absence of police documentation "
            "is a primary fraud indicator in vehicle insurance claims."
        )
    else:
        evidence_parts.append(
            "Police report filed — law enforcement documentation present, "
            "supporting claim legitimacy."
        )

    if str(witness).strip().lower() == "no":
        evidence_parts.append(
            "No witnesses present to corroborate the incident — "
            "unwitnessed accidents have higher fraud association."
        )
    else:
        evidence_parts.append(
            "Witnesses present to corroborate the incident — "
            "independent verification supports claim legitimacy."
        )

    if str(agent_type).strip().lower() == "external":
        evidence_parts.append(
            "Handled by external agent — external agents show statistically "
            "elevated fraud rates compared to internal agents."
        )
    else:
        evidence_parts.append(
            "Handled by internal agent — internal agent involvement "
            "associated with lower fraud rates."
        )

    if str(past_claims).strip().lower() not in ["none", "0", ""]:
        evidence_parts.append(
            f"Repeat claimant with {past_claims} prior claims — "
            "multiple prior claims indicate potential repeat fraud pattern."
        )
    else:
        evidence_parts.append(
            "No prior claims history — first-time claimant profile."
        )

    if str(supplements).strip().lower() not in ["none", "0", ""]:
        evidence_parts.append(
            f"Repair supplements: {supplements} — "
            "elevated supplement count suggests potentially inflated repair costs."
        )
    else:
        evidence_parts.append(
            "No repair supplements — standard repair cost profile."
        )

    if str(address_change).strip().lower() not in ["no change", "none", ""]:
        evidence_parts.append(
            f"Address change near claim time: {address_change} — "
            "address changes around claim filing are a fraud risk indicator."
        )

    if str(day).strip().lower() in ["saturday", "sunday"]:
        evidence_parts.append(
            f"Weekend accident ({day}) — weekend incidents with no witnesses "
            "are associated with staged accident patterns."
        )

    if str(driver_rating) == "4":
        evidence_parts.append(
            "Driver rating 4 (worst category) — poor driver rating "
            "correlates with elevated fraud risk."
        )

    if str(days_accident).strip().lower() in ["1 to 7", "8 to 15"]:
        evidence_parts.append(
            f"Policy was active only {days_accident} before accident — "
            "very new policy at time of accident suggests potential policy gaming."
        )
    else:
        evidence_parts.append(
            f"Policy active {days_accident} before accident — "
            "established policy duration reduces gaming suspicion."
        )

    evidence_text = " ".join(evidence_parts[:5])

    # ── Fraud signals section ───────────────────────────────────────────────────
    if fraud_signals:
        signals_text = f"Fraud signals detected: {', '.join(fraud_signals[:6])}."
    else:
        signals_text = "No fraud signals detected."

    # ── Engineered feature vocabulary ──────────────────────────────────────────
    # These phrases improve semantic matching for combined risk patterns
    fe_parts = []
    if no_evidence:
        fe_parts.append("NO_EVIDENCE_PATTERN: no police report and no witnesses combined")
    if is_high_value_claim:
        fe_parts.append("HIGH_VALUE_CLAIM: vehicle price exceeds 60000")
    if is_new_policy:
        fe_parts.append("NEW_POLICY_QUICK_CLAIM: policy active less than 7 days before accident")
    if is_repeat_claimant:
        fe_parts.append("REPEAT_CLAIMANT_PATTERN: multiple prior claims history")
    if has_excess_supplements:
        fe_parts.append("EXCESS_SUPPLEMENTS_PATTERN: repair supplements 3 or more")
    if is_old_high_vehicle:
        fe_parts.append("OLD_HIGH_VALUE_VEHICLE: aged vehicle with high claim amount")
    if recent_address_change:
        fe_parts.append("RECENT_ADDRESS_CHANGE: address changed within 6 months of claim")
    if is_external_agent:
        fe_parts.append("EXTERNAL_AGENT_INVOLVEMENT: claim handled by external agent")
    if is_weekend:
        fe_parts.append("WEEKEND_ACCIDENT: accident occurred on weekend")
    if fraud_risk_flags > 0:
        fe_parts.append(f"FRAUD_RISK_FLAGS: {fraud_risk_flags} out of 9 risk indicators active")

    fe_text = " ".join(fe_parts) if fe_parts else ""

    # ── Core claim facts ────────────────────────────────────────────────────────
    facts = (
        f"Claim {policy_num}: {vehicle_cat} {make} vehicle, "
        f"priced {vehicle_price}, aged {age_vehicle}. "
        f"{accident_area} area accident on {day} in {month} {year}. "
        f"Policy type: {base_policy}. "
        f"Fault: {fault}. "
        f"Deductible: ${deductible}. "
        f"Policyholder: {sex}, {marital}, aged {age_holder}. "
        f"Claim filed {days_claim} after accident."
    )

    # ── Assemble full narrative ─────────────────────────────────────────────────
    parts = [
        f"{outcome_header}. {outcome_text}",
        facts,
        evidence_text,
        signals_text,
    ]
    if fe_text:
        parts.append(fe_text)

    narrative = " ".join(parts)
    return narrative.strip()


def _get_accident_type(row: dict) -> str:
    """Extract accident type from policy type field."""
    policy_type = row.get("PolicyType", row.get("policy_type", ""))
    if not policy_type:
        return "vehicle"
    type_lower = str(policy_type).lower()
    if "collision" in type_lower:
        return "collision"
    elif "liability" in type_lower:
        return "liability"
    elif "all perils" in type_lower:
        return "multi-peril"
    return "vehicle"
