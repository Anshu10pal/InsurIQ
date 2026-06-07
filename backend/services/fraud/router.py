"""Fraud scoring router."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.fraud.scoring.rule_engine import evaluate_rules
from services.fraud.scoring.statistical_scorer import compute_statistical_flags
from services.fraud.scoring.risk_calculator import calculate_risk_score, get_risk_level

router = APIRouter()


class ScoreRequest(BaseModel):
    policy_number: Optional[int] = None
    make: Optional[str] = None
    vehicle_category: Optional[str] = None
    vehicle_price: Optional[str] = None
    age_of_vehicle: Optional[str] = None
    accident_area: Optional[str] = None
    fault: Optional[str] = None
    base_policy: Optional[str] = None
    police_report_filed: Optional[str] = "No"
    witness_present: Optional[str] = "No"
    agent_type: Optional[str] = "External"
    days_policy_accident: Optional[str] = "more than 30"
    days_policy_claim: Optional[str] = "more than 30"
    past_number_of_claims: Optional[str] = "none"
    number_of_supplements: Optional[str] = "none"
    address_change_claim: Optional[str] = "no change"
    number_of_cars: Optional[str] = "1 vehicle"
    day_of_week: Optional[str] = "Monday"
    driver_rating: Optional[int] = 1
    deductible: Optional[int] = 400


@router.post("/score-new-claim")
def score_new_claim(request: ScoreRequest):
    claim = {
        "VehicleCategory": request.vehicle_category, "VehiclePrice": request.vehicle_price,
        "AgeOfVehicle": request.age_of_vehicle, "AccidentArea": request.accident_area,
        "Fault": request.fault, "BasePolicy": request.base_policy,
        "PoliceReportFiled": request.police_report_filed, "WitnessPresent": request.witness_present,
        "AgentType": request.agent_type, "Days_Policy_Accident": request.days_policy_accident,
        "Days_Policy_Claim": request.days_policy_claim, "PastNumberOfClaims": request.past_number_of_claims,
        "NumberOfSupplements": request.number_of_supplements, "AddressChange_Claim": request.address_change_claim,
        "NumberOfCars": request.number_of_cars, "DayOfWeek": request.day_of_week,
        "DriverRating": request.driver_rating, "Deductible": request.deductible, "Make": request.make,
    }
    signals = evaluate_rules(claim)
    stat_flags = compute_statistical_flags(claim)
    score = calculate_risk_score(signals, stat_flags, claim)
    return {"risk_score": score, "risk_level": get_risk_level(score),
            "fraud_signals": signals, "statistical_flags": stat_flags}
