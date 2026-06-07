import psycopg2
import os
import json
from fastapi import APIRouter

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats():
    conn = psycopg2.connect(
        os.getenv("DATABASE_URL", "postgresql://insuriq_user:root123@localhost:5432/insuriq")
    )
    cur = conn.cursor()
    try:
        # --- summary counts ---
        cur.execute("SELECT COUNT(*) FROM claims")
        total_claims = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM claims WHERE fraud_found_p = 1")
        fraud_claims = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM claims WHERE fraud_risk_score >= 70")
        high_risk = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM claims WHERE fraud_risk_score BETWEEN 40 AND 69")
        medium_risk = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM claims WHERE fraud_risk_score < 40")
        low_risk = cur.fetchone()[0] or 0

        # --- fraud by area ---
        cur.execute(
            "SELECT accident_area, COUNT(*), SUM(fraud_found_p) "
            "FROM claims WHERE accident_area IS NOT NULL "
            "GROUP BY accident_area ORDER BY 2 DESC"
        )
        area_stats = cur.fetchall()

        # --- fraud by vehicle ---
        cur.execute(
            "SELECT vehicle_category, COUNT(*), SUM(fraud_found_p) "
            "FROM claims WHERE vehicle_category IS NOT NULL "
            "GROUP BY vehicle_category ORDER BY 2 DESC"
        )
        vehicle_stats = cur.fetchall()

        # --- fraud by agent ---
        cur.execute(
            "SELECT agent_type, COUNT(*), SUM(fraud_found_p) "
            "FROM claims WHERE agent_type IS NOT NULL "
            "GROUP BY agent_type ORDER BY 2 DESC"
        )
        agent_stats = cur.fetchall()

        # --- fraud by day ---
        cur.execute(
            "SELECT day_of_week, COUNT(*), SUM(fraud_found_p) "
            "FROM claims WHERE day_of_week IS NOT NULL "
            "GROUP BY day_of_week "
            "ORDER BY CASE day_of_week "
            "WHEN 'Monday'    THEN 1 WHEN 'Tuesday'  THEN 2 "
            "WHEN 'Wednesday' THEN 3 WHEN 'Thursday' THEN 4 "
            "WHEN 'Friday'    THEN 5 WHEN 'Saturday' THEN 6 "
            "WHEN 'Sunday'    THEN 7 ELSE 8 END"
        )
        day_stats = cur.fetchall()

        # --- fraud by policy duration ---
        cur.execute(
            "SELECT days_policy_accident, COUNT(*), SUM(fraud_found_p) "
            "FROM claims WHERE days_policy_accident IS NOT NULL "
            "GROUP BY days_policy_accident "
            "ORDER BY CASE days_policy_accident "
            "WHEN 'none'         THEN 1 WHEN '1 to 7'      THEN 2 "
            "WHEN '8 to 15'      THEN 3 WHEN '15 to 30'    THEN 4 "
            "WHEN 'more than 30' THEN 5 ELSE 6 END"
        )
        policy_duration_stats = cur.fetchall()

        # --- top fraud signals (::text cast fix applied) ---
        cur.execute(
            "SELECT fraud_signals FROM claims "
            "WHERE fraud_found_p = 1 "
            "AND fraud_signals IS NOT NULL "
            "AND fraud_signals::text != '[]' "
            "LIMIT 2000"
        )
        signal_rows = cur.fetchall()
        signal_freq: dict = {}
        for row in signal_rows:
            try:
                signals = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                if isinstance(signals, list):
                    for sig in signals:
                        signal_freq[sig] = signal_freq.get(sig, 0) + 1
            except Exception:
                pass
        top_signals = sorted(signal_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        # --- claims by year ---
        cur.execute(
            "SELECT year, COUNT(*), SUM(fraud_found_p) "
            "FROM claims WHERE year IS NOT NULL "
            "GROUP BY year ORDER BY year ASC"
        )
        year_stats = cur.fetchall()

        # --- high risk claims ---
        cur.execute(
            "SELECT policy_number, make, vehicle_category, accident_area, "
            "fraud_risk_score, fraud_found_p "
            "FROM claims WHERE fraud_risk_score >= 70 "
            "ORDER BY fraud_risk_score DESC LIMIT 10"
        )
        high_risk_claims = cur.fetchall()

        return {
            "summary": {
                "total_claims":    total_claims,
                "fraud_claims":    fraud_claims,
                "fraud_rate":      round(fraud_claims / total_claims * 100, 2) if total_claims else 0,
                "high_risk_count": high_risk,
                "medium_risk_count": medium_risk,
                "low_risk_count":  low_risk,
            },
            "fraud_by_area": [
                {"area": r[0], "total": r[1], "fraud_count": r[2],
                 "fraud_rate": round(r[2] / r[1] * 100, 1) if r[1] else 0}
                for r in area_stats
            ],
            "fraud_by_vehicle": [
                {"category": r[0], "total": r[1], "fraud_count": r[2],
                 "fraud_rate": round(r[2] / r[1] * 100, 1) if r[1] else 0}
                for r in vehicle_stats
            ],
            "fraud_by_agent": [
                {"agent": r[0], "total": r[1], "fraud_count": r[2],
                 "fraud_rate": round(r[2] / r[1] * 100, 1) if r[1] else 0}
                for r in agent_stats
            ],
            "fraud_by_day": [
                {"day": r[0][:3], "total": r[1], "fraud_count": r[2],
                 "fraud_rate": round(r[2] / r[1] * 100, 1) if r[1] else 0}
                for r in day_stats
            ],
            "fraud_by_policy_duration": [
                {"duration": r[0], "total": r[1], "fraud_count": r[2],
                 "fraud_rate": round(r[2] / r[1] * 100, 1) if r[1] else 0}
                for r in policy_duration_stats
            ],
            "top_fraud_signals": [
                {"signal": s[0].replace("_", " "), "count": s[1]}
                for s in top_signals
            ],
            "claims_by_year": [
                {"year": r[0], "total": r[1], "fraud_count": r[2],
                 "fraud_rate": round(r[2] / r[1] * 100, 1) if r[1] else 0}
                for r in year_stats
            ],
            "high_risk_claims": [
                {
                    "policy_number":   r[0],
                    "make":            r[1],
                    "vehicle_category": r[2],
                    "accident_area":   r[3],
                    "fraud_risk_score": r[4],
                    "fraud_found_p":   r[5],
                    "fraud_signals":   [],
                }
                for r in high_risk_claims
            ],
        }
    finally:
        cur.close()
        conn.close()
