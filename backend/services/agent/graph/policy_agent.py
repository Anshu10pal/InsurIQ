"""Agent 3 — policy validation agent."""
from services.agent.graph.state import ClaimInvestigationState
from utils.logging import get_logger

logger = get_logger(__name__)


def policy_agent(state: ClaimInvestigationState) -> ClaimInvestigationState:
    logger.info("policy_agent_started")
    state["current_agent"] = "policy_validation"
    try:
        retrieved_claims = state.get("retrieved_claims", [])
        issues = []
        for claim in retrieved_claims:
            days_claim = str(claim.get("days_policy_claim") or claim.get("Days_Policy_Claim") or "")
            days_accident = str(claim.get("days_policy_accident") or claim.get("Days_Policy_Accident") or "")
            age_vehicle = str(claim.get("age_of_vehicle") or claim.get("AgeOfVehicle") or "")
            base_policy = str(claim.get("base_policy") or claim.get("BasePolicy") or "")
            is_new = claim.get("is_new_policy", 0)

            if days_claim in ["none", "1 to 7"] and days_accident in ["more than 30"]:
                issues.append("CLAIM_FILED_BEFORE_ACCIDENT: Timeline inconsistency detected")
            if age_vehicle == "more than 7" and "All Perils" in base_policy:
                issues.append("OLD_VEHICLE_COMPREHENSIVE: Vehicle age inconsistent with All Perils policy")
            if is_new or days_accident in ["none", "1 to 7"]:
                if "more than 30" not in (days_accident or ""):
                    pass

        unique_issues = list(dict.fromkeys(issues))
        state["policy_issues"] = unique_issues[:4]
        state["completed_agents"] = state.get("completed_agents", []) + ["policy_validation"]
        logger.info("policy_agent_complete", issues_found=len(unique_issues))
    except Exception as e:
        logger.error("policy_agent_failed", error=str(e))
        state["policy_issues"] = []
    return state
