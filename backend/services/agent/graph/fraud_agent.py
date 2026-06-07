"""
Fraud analyst agent — frequency-weighted signal scoring.

Formula (fixed):
    Part 1 — Signal weight × frequency ratio (max 60 pts)
        Uses SIGNAL_WEIGHTS from signal_definitions.
        Frequency ratio = how many of the 5 retrieved claims show that signal.
        Critical combination bonuses on top.
        Capped at 60.

    Part 2 — Average pre-computed score (max 20 pts)
        avg_fraud_risk_score of retrieved claims × 0.20

    Part 3 — Statistical anomaly rate (max 15 pts)
        % of retrieved claims with anomaly flags × 15

    Floor boost — confirmed fraud claims push score up
        If majority of retrieved claims are confirmed fraud, apply floor.

Total max = 95 pts

Expected:
    HIGH risk query  → confirmed fraud claims, many signals  → 70-95
    MEDIUM risk      → mixed fraud, some signals             → 40-65
    LOW risk query   → clean claims, few/no signals          → 10-30
"""
from services.agent.graph.state import ClaimInvestigationState
from services.fraud.scoring.statistical_scorer import compute_statistical_flags
from services.fraud.scoring.risk_calculator import get_risk_level
from services.fraud.scoring.signal_definitions import SIGNAL_WEIGHTS
from utils.logging import get_logger

logger = get_logger(__name__)


def fraud_agent(state: ClaimInvestigationState) -> ClaimInvestigationState:
    logger.info("fraud_agent_started")
    state["current_agent"] = "fraud_analysis"

    try:
        retrieved_claims = state.get("retrieved_claims", [])

        if not retrieved_claims:
            state["fraud_signals"]        = []
            state["statistical_flags"]    = []
            state["fraud_score"]          = 0
            state["risk_level"]           = "LOW"
            state["cross_claim_patterns"] = []
            state["completed_agents"]     = state.get("completed_agents", []) + ["fraud_analysis"]
            return state

        total_claims = len(retrieved_claims)

        # ── Build signal frequency map ──────────────────────────────────────
        signal_frequency: dict = {}
        all_flags = []

        for claim in retrieved_claims:
            signals = claim.get("fraud_signals") or []
            if isinstance(signals, str):
                import json
                try:
                    signals = json.loads(signals)
                except Exception:
                    signals = []
            for signal in signals:
                signal_frequency[signal] = signal_frequency.get(signal, 0) + 1
            flags = compute_statistical_flags(claim)
            all_flags.extend(flags)

        # ── Part 1: Signal weight × frequency ratio (max 60) ───────────────
        # Core: weight each signal by how often it appears across retrieved claims
        raw_part1 = 0.0
        for signal, freq in signal_frequency.items():
            weight          = SIGNAL_WEIGHTS.get(signal, 5)
            frequency_ratio = freq / total_claims
            raw_part1      += weight * frequency_ratio

        # Combination bonuses — patterns that strongly indicate fraud
        no_police_rate   = sum(1 for c in retrieved_claims if "HIGH_AMOUNT_NO_POLICE_REPORT" in (c.get("fraud_signals") or [])) / total_claims
        no_witness_rate  = sum(1 for c in retrieved_claims if "WEEKEND_NO_WITNESS"           in (c.get("fraud_signals") or [])) / total_claims
        new_policy_rate  = sum(1 for c in retrieved_claims if "NEW_POLICY_QUICK_CLAIM"       in (c.get("fraud_signals") or [])) / total_claims
        repeat_rate      = sum(1 for c in retrieved_claims if "HIGH_PRIOR_CLAIMS"            in (c.get("fraud_signals") or [])) / total_claims
        urban_rate       = sum(1 for c in retrieved_claims if "URBAN_NO_EVIDENCE"            in (c.get("fraud_signals") or [])) / total_claims

        bonus = (
            no_police_rate  * 6.0 +
            no_witness_rate * 4.0 +
            new_policy_rate * 5.0 +
            repeat_rate     * 4.0 +
            urban_rate      * 3.0
        )

        part1 = min(round(raw_part1 + bonus), 60)

        # ── Part 2: Pre-computed score average (max 20) ─────────────────────
        avg_precomputed = sum(
            float(c.get("fraud_risk_score") or 0)
            for c in retrieved_claims
        ) / total_claims
        part2 = round((avg_precomputed / 100.0) * 20)

        # ── Part 3: Statistical anomaly rate (max 15) ───────────────────────
        def claim_has_anomaly(c: dict) -> bool:
            if compute_statistical_flags(c):
                return True
            if int(c.get("is_old_high_vehicle",   0) or 0):
                return True
            if int(c.get("recent_address_change", 0) or 0):
                return True
            return False

        claims_with_anomaly = sum(1 for c in retrieved_claims if claim_has_anomaly(c))
        part3 = round((claims_with_anomaly / total_claims) * 15)

        # ── Confirmed fraud floor boost ──────────────────────────────────────
        # If majority of retrieved claims are confirmed fraud, don't let
        # the score sit below MEDIUM — the retrieval itself is strong signal.
        confirmed_fraud_rate = sum(
            1 for c in retrieved_claims if int(c.get("fraud_found_p") or 0) == 1
        ) / total_claims

        raw_final = part1 + part2 + part3

        # Apply floor: if >60% confirmed fraud in retrieved set, score >= 55
        # If >80% confirmed fraud, score >= 70
        if confirmed_fraud_rate >= 0.80:
            raw_final = max(raw_final, 70)
        elif confirmed_fraud_rate >= 0.60:
            raw_final = max(raw_final, 55)

        final_score = max(0, min(100, raw_final))

        # ── Signals ordered by frequency ────────────────────────────────────
        unique_signals = list(dict.fromkeys(
            sorted(signal_frequency.keys(),
                   key=lambda s: signal_frequency[s], reverse=True)
        ))
        unique_flags = list(dict.fromkeys(all_flags))

        cross_claim_patterns = [
            f"{signal} (seen in {count}/{total_claims} similar claims)"
            for signal, count in sorted(
                signal_frequency.items(),
                key=lambda x: x[1], reverse=True
            )
            if count >= 2
        ]

        state["fraud_signals"]        = unique_signals
        state["statistical_flags"]    = unique_flags
        state["fraud_score"]          = final_score
        state["risk_level"]           = get_risk_level(final_score)
        state["cross_claim_patterns"] = cross_claim_patterns
        state["completed_agents"]     = state.get("completed_agents", []) + ["fraud_analysis"]

        logger.info(
            "fraud_agent_complete",
            risk_score=final_score,
            risk_level=get_risk_level(final_score),
            part1_signals=part1,
            part2_avg_score=part2,
            part3_anomaly=part3,
            confirmed_fraud_rate=round(confirmed_fraud_rate, 2),
            avg_precomputed=round(avg_precomputed, 1),
            signal_count=len(unique_signals),
        )

    except Exception as e:
        logger.error("fraud_agent_failed", error=str(e))
        state["fraud_signals"]        = []
        state["statistical_flags"]    = []
        state["fraud_score"]          = 0
        state["risk_level"]           = "UNKNOWN"
        state["cross_claim_patterns"] = []
        state["warning"]              = f"Fraud analysis degraded: {str(e)}"
        state["partial_result"]       = True

    return state