"""Statistical thresholds from EDA analysis."""
VEHICLE_PRICE_THRESHOLDS = {
    "Sport": {"mean": 49500, "std": 18000},
    "Utility": {"mean": 34500, "std": 15000},
    "Sedan": {"mean": 29000, "std": 12000},
}
SUPPLEMENTS_SUSPICIOUS_THRESHOLD = 3
PAST_CLAIMS_SUSPICIOUS_THRESHOLD = 3
ADDRESS_CHANGE_SUSPICIOUS_THRESHOLD = 1
DAYS_TO_CLAIM_SUSPICIOUS = 7
BASE_POLICY_FRAUD_RATES = {"All Perils": 0.07, "Collision": 0.05, "Liability": 0.06}
FAULT_FRAUD_RATES = {"Policy Holder": 0.07, "Third Party": 0.04}
AGENT_TYPE_FRAUD_RATES = {"External": 0.07, "Internal": 0.04}
ACCIDENT_AREA_FRAUD_RATES = {"Urban": 0.06, "Rural": 0.05}
Z_SCORE_THRESHOLD = 2.0

def get_base_rate(field: str, value: str) -> float:
    rate_maps = {
        "BasePolicy": BASE_POLICY_FRAUD_RATES,
        "Fault": FAULT_FRAUD_RATES,
        "AgentType": AGENT_TYPE_FRAUD_RATES,
        "AccidentArea": ACCIDENT_AREA_FRAUD_RATES,
    }
    if field not in rate_maps:
        return 0.06
    return rate_maps[field].get(value, 0.06)
