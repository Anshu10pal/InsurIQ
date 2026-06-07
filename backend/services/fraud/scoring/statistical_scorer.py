"""Statistical scorer — z-score anomaly detection."""
from typing import List, Dict, Any
from services.ingestion.ordinal_maps import encode_ordinal
from services.ingestion.thresholds import (
    VEHICLE_PRICE_THRESHOLDS, SUPPLEMENTS_SUSPICIOUS_THRESHOLD,
    PAST_CLAIMS_SUSPICIOUS_THRESHOLD, ADDRESS_CHANGE_SUSPICIOUS_THRESHOLD,
    DAYS_TO_CLAIM_SUSPICIOUS, Z_SCORE_THRESHOLD,
)


def compute_statistical_flags(claim: Dict[str, Any]) -> List[str]:
    flags = []
    def get(f, s=None, d=None): return claim.get(f) or claim.get(s or f.lower(), d)

    vehicle_category = str(get("VehicleCategory", "vehicle_category") or "Sedan")
    vehicle_price_raw = str(get("VehiclePrice", "vehicle_price") or "less than 20000")
    vehicle_price_num = encode_ordinal("VehiclePrice", vehicle_price_raw)
    category_thresholds = VEHICLE_PRICE_THRESHOLDS.get(vehicle_category, {"mean": 34500, "std": 15000})
    std = category_thresholds["std"]
    if std > 0:
        price_z = (vehicle_price_num - category_thresholds["mean"]) / std
        if price_z > Z_SCORE_THRESHOLD:
            flags.append(f"ANOMALOUS_VEHICLE_PRICE (z={price_z:.2f})")

    supplements_raw = str(get("NumberOfSupplements", "number_of_supplements") or get("NumberOfSuppliments", "number_of_suppliments") or "none")
    supplements_num = encode_ordinal("NumberOfSuppliments", supplements_raw)
    if supplements_num > SUPPLEMENTS_SUSPICIOUS_THRESHOLD:
        flags.append(f"HIGH_SUPPLEMENTS_COUNT ({supplements_num} supplements)")

    past_claims_raw = str(get("PastNumberOfClaims", "past_number_of_claims") or "none")
    past_claims_num = encode_ordinal("PastNumberOfClaims", past_claims_raw)
    if past_claims_num >= PAST_CLAIMS_SUSPICIOUS_THRESHOLD:
        flags.append(f"HIGH_PAST_CLAIMS_COUNT ({past_claims_num} claims)")

    return flags


def compute_base_rate_component(claim: Dict[str, Any]) -> float:
    from services.ingestion.thresholds import BASE_POLICY_FRAUD_RATES, AGENT_TYPE_FRAUD_RATES, ACCIDENT_AREA_FRAUD_RATES
    def get(f, s=None, d=None): return claim.get(f) or claim.get(s or f.lower(), d)
    base_rate = BASE_POLICY_FRAUD_RATES.get(str(get("BasePolicy", "base_policy") or ""), 0.06)
    agent_rate = AGENT_TYPE_FRAUD_RATES.get(str(get("AgentType", "agent_type") or ""), 0.06)
    area_rate = ACCIDENT_AREA_FRAUD_RATES.get(str(get("AccidentArea", "accident_area") or ""), 0.06)
    return (base_rate + agent_rate + area_rate) / 3
