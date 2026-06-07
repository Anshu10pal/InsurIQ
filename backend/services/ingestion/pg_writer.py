"""
PostgreSQL writer — bulk upserts claim records into PostgreSQL.
Also triggers ChromaDB upsert for vector search.

Uses raw SQL INSERT ... ON CONFLICT DO UPDATE to avoid SQLAlchemy
parameter limit issues with 44-column tables.

Updated: renamed number_of_suppliments -> number_of_supplements
         added 10 engineered feature columns
         replaced SQLAlchemy insert with raw SQL to fix parameter limit
"""
import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from utils.logging import get_logger
from utils.resilience import retry_db

logger = get_logger(__name__)


def _map_record_to_claim(
    record: dict,
    narrative: str,
    fraud_score: int,
    fraud_signals: List[str],
    statistical_flags: List[str],
) -> dict:
    """Map a raw CSV record dict to Claim model fields."""

    def get_supplements():
        return (
            record.get("NumberOfSupplements") or
            record.get("NumberOfSuppliments") or
            ""
        )

    def fe(new_key, old_key=None, default=0):
        v = record.get(new_key, record.get(old_key or new_key, default))
        try:
            return int(v) if v is not None else default
        except (ValueError, TypeError):
            return default

    return {
        "policy_number":          int(record.get("PolicyNumber", 0)),
        "month":                  record.get("Month"),
        "week_of_month":          record.get("WeekOfMonth"),
        "day_of_week":            record.get("DayOfWeek"),
        "day_of_week_claimed":    record.get("DayOfWeekClaimed"),
        "month_claimed":          record.get("MonthClaimed"),
        "week_of_month_claimed":  record.get("WeekOfMonthClaimed"),
        "year":                   record.get("Year"),
        "make":                   record.get("Make"),
        "vehicle_category":       record.get("VehicleCategory"),
        "vehicle_price":          record.get("VehiclePrice"),
        "age_of_vehicle":         record.get("AgeOfVehicle"),
        "accident_area":          record.get("AccidentArea"),
        "fault":                  record.get("Fault"),
        "policy_type":            record.get("PolicyType"),
        "base_policy":            record.get("BasePolicy"),
        "sex":                    record.get("Sex"),
        "marital_status":         record.get("MaritalStatus"),
        "age":                    record.get("Age"),
        "age_of_policy_holder":   record.get("AgeOfPolicyHolder"),
        "deductible":             record.get("Deductible"),
        "driver_rating":          record.get("DriverRating"),
        "days_policy_accident":   record.get("Days_Policy_Accident"),
        "days_policy_claim":      record.get("Days_Policy_Claim"),
        "past_number_of_claims":  record.get("PastNumberOfClaims"),
        "number_of_supplements":  get_supplements(),
        "address_change_claim":   record.get("AddressChange_Claim"),
        "number_of_cars":         record.get("NumberOfCars"),
        "police_report_filed":    record.get("PoliceReportFiled"),
        "witness_present":        record.get("WitnessPresent"),
        "rep_number":             record.get("RepNumber"),
        "agent_type":             record.get("AgentType"),
        "fraud_found_p":          int(record.get("FraudFound_P", 0)),
        "claim_narrative":        narrative,
        "fraud_risk_score":       fraud_score,
        "fraud_signals":          json.dumps(fraud_signals),
        "statistical_flags":      json.dumps(statistical_flags),
        "is_weekend":             fe("IsWeekend",            "is_weekend"),
        "no_evidence":            fe("NoEvidence",           "no_evidence"),
        "is_high_value_claim":    fe("IsHighValueClaim",     "is_high_value_claim"),
        "is_new_policy":          fe("IsNewPolicy",          "is_new_policy"),
        "is_repeat_claimant":     fe("IsRepeatClaimant",     "is_repeat_claimant"),
        "has_excess_supplements": fe("HasExcessSupplements", "has_excess_supplements"),
        "is_old_high_vehicle":    fe("IsOldHighValueVehicle","is_old_high_vehicle"),
        "recent_address_change":  fe("RecentAddressChange",  "recent_address_change"),
        "is_external_agent":      fe("IsExternalAgent",      "is_external_agent"),
        "fraud_risk_flags":       fe("FraudRiskFlags",       "fraud_risk_flags"),
    }


def _build_chroma_metadata(
    record: dict,
    fraud_score: int,
    fraud_signals: List[str],
) -> dict:
    """Build metadata dict for ChromaDB storage."""

    def fe(new_key, old_key=None, default=0):
        v = record.get(new_key, record.get(old_key or new_key, default))
        try:
            return int(v) if v is not None else default
        except (ValueError, TypeError):
            return default

    def get_supplements():
        return str(
            record.get("NumberOfSupplements") or
            record.get("NumberOfSuppliments") or
            ""
        )

    return {
        "accident_area":          str(record.get("AccidentArea") or ""),
        "base_policy":            str(record.get("BasePolicy") or ""),
        "vehicle_category":       str(record.get("VehicleCategory") or ""),
        "make":                   str(record.get("Make") or ""),
        "fault":                  str(record.get("Fault") or ""),
        "police_report_filed":    str(record.get("PoliceReportFiled") or ""),
        "witness_present":        str(record.get("WitnessPresent") or ""),
        "agent_type":             str(record.get("AgentType") or ""),
        "past_number_of_claims":  str(record.get("PastNumberOfClaims") or ""),
        "number_of_supplements":  get_supplements(),
        "address_change_claim":   str(record.get("AddressChange_Claim") or ""),
        "vehicle_price":          str(record.get("VehiclePrice") or ""),
        "age_of_vehicle":         str(record.get("AgeOfVehicle") or ""),
        "fraud_found_p":          int(record.get("FraudFound_P", 0)),
        "fraud_risk_score":       fraud_score,
        "fraud_signals":          json.dumps(fraud_signals),
        "year":                   int(record.get("Year") or 0),
        "is_weekend":             fe("IsWeekend",            "is_weekend"),
        "no_evidence":            fe("NoEvidence",           "no_evidence"),
        "is_high_value_claim":    fe("IsHighValueClaim",     "is_high_value_claim"),
        "is_new_policy":          fe("IsNewPolicy",          "is_new_policy"),
        "is_repeat_claimant":     fe("IsRepeatClaimant",     "is_repeat_claimant"),
        "has_excess_supplements": fe("HasExcessSupplements", "has_excess_supplements"),
        "is_old_high_vehicle":    fe("IsOldHighValueVehicle","is_old_high_vehicle"),
        "recent_address_change":  fe("RecentAddressChange",  "recent_address_change"),
        "is_external_agent":      fe("IsExternalAgent",      "is_external_agent"),
        "fraud_risk_flags":       fe("FraudRiskFlags",       "fraud_risk_flags"),
    }


# Raw SQL upsert — avoids SQLAlchemy parameter limit with 44-column tables
_UPSERT_SQL = text("""
INSERT INTO claims (
    policy_number, month, week_of_month, day_of_week, day_of_week_claimed,
    month_claimed, week_of_month_claimed, year, make, vehicle_category,
    vehicle_price, age_of_vehicle, accident_area, fault, policy_type,
    base_policy, sex, marital_status, age, age_of_policy_holder,
    deductible, driver_rating, days_policy_accident, days_policy_claim,
    past_number_of_claims, number_of_supplements, address_change_claim,
    number_of_cars, police_report_filed, witness_present, rep_number,
    agent_type, fraud_found_p, claim_narrative, fraud_risk_score,
    fraud_signals, statistical_flags,
    is_weekend, no_evidence, is_high_value_claim, is_new_policy,
    is_repeat_claimant, has_excess_supplements, is_old_high_vehicle,
    recent_address_change, is_external_agent, fraud_risk_flags
) VALUES (
    :policy_number, :month, :week_of_month, :day_of_week, :day_of_week_claimed,
    :month_claimed, :week_of_month_claimed, :year, :make, :vehicle_category,
    :vehicle_price, :age_of_vehicle, :accident_area, :fault, :policy_type,
    :base_policy, :sex, :marital_status, :age, :age_of_policy_holder,
    :deductible, :driver_rating, :days_policy_accident, :days_policy_claim,
    :past_number_of_claims, :number_of_supplements, :address_change_claim,
    :number_of_cars, :police_report_filed, :witness_present, :rep_number,
    :agent_type, :fraud_found_p, :claim_narrative, :fraud_risk_score,
    CAST(:fraud_signals AS json), CAST(:statistical_flags AS json),
    :is_weekend, :no_evidence, :is_high_value_claim, :is_new_policy,
    :is_repeat_claimant, :has_excess_supplements, :is_old_high_vehicle,
    :recent_address_change, :is_external_agent, :fraud_risk_flags
)
ON CONFLICT (policy_number) DO UPDATE SET
    claim_narrative        = EXCLUDED.claim_narrative,
    fraud_risk_score       = EXCLUDED.fraud_risk_score,
    fraud_signals          = EXCLUDED.fraud_signals,
    statistical_flags      = EXCLUDED.statistical_flags,
    number_of_supplements  = EXCLUDED.number_of_supplements,
    is_weekend             = EXCLUDED.is_weekend,
    no_evidence            = EXCLUDED.no_evidence,
    is_high_value_claim    = EXCLUDED.is_high_value_claim,
    is_new_policy          = EXCLUDED.is_new_policy,
    is_repeat_claimant     = EXCLUDED.is_repeat_claimant,
    has_excess_supplements = EXCLUDED.has_excess_supplements,
    is_old_high_vehicle    = EXCLUDED.is_old_high_vehicle,
    recent_address_change  = EXCLUDED.recent_address_change,
    is_external_agent      = EXCLUDED.is_external_agent,
    fraud_risk_flags       = EXCLUDED.fraud_risk_flags
""")


@retry_db
def bulk_upsert_claims(
    db: Session,
    records: List[Dict[str, Any]],
    narratives: List[str],
    embeddings: List[List[float]],
    fraud_scores: List[int],
    fraud_signals_list: List[List[str]],
    statistical_flags_list: List[List[str]],
    batch_size: int = 500,
) -> int:
    """
    Bulk upsert claim records into PostgreSQL + ChromaDB.
    Uses raw SQL to avoid SQLAlchemy parameter limit with 44-column tables.
    """
    from services.rag.chroma_client import upsert_embeddings

    total_upserted = 0

    # Step 1 — PostgreSQL bulk upsert using raw SQL
    for batch_start in range(0, len(records), batch_size):
        batch_records    = records[batch_start:batch_start + batch_size]
        batch_narratives = narratives[batch_start:batch_start + batch_size]
        batch_scores     = fraud_scores[batch_start:batch_start + batch_size]
        batch_signals    = fraud_signals_list[batch_start:batch_start + batch_size]
        batch_flags      = statistical_flags_list[batch_start:batch_start + batch_size]

        mapped = [
            _map_record_to_claim(rec, nar, score, signals, flags)
            for rec, nar, score, signals, flags in zip(
                batch_records, batch_narratives,
                batch_scores, batch_signals, batch_flags
            )
        ]

        # Execute one row at a time using raw SQL — no parameter limit
        for row in mapped:
            db.execute(_UPSERT_SQL, row)

        db.commit()
        total_upserted += len(mapped)

        logger.info(
            "pg_batch_upserted",
            batch_start=batch_start,
            batch_size=len(mapped),
            total_so_far=total_upserted,
        )

    # Step 2 — ChromaDB upsert
    logger.info("writing_to_chromadb", total=len(records))
    policy_numbers = [int(r.get("PolicyNumber", 0)) for r in records]
    metadatas = [
        _build_chroma_metadata(r, s, sig)
        for r, s, sig in zip(records, fraud_scores, fraud_signals_list)
    ]

    upsert_embeddings(
        policy_numbers=policy_numbers,
        embeddings=embeddings,
        narratives=narratives,
        metadatas=metadatas,
    )

    logger.info("bulk_upsert_complete", total_upserted=total_upserted)
    return total_upserted
