from locust import HttpUser, task, between


class InvestigationUser(HttpUser):
    """Simulates users running fraud investigations."""
    wait_time = between(2, 5)
    host = "http://localhost:8000"

    @task(3)
    def investigate(self):
        self.client.post(
            "/api/v1/claims/investigate",
            json={"query": "suspicious claims no police report external agent urban high vehicle price"},
            timeout=60,
        )

    @task(1)
    def score_claim(self):
        self.client.post(
            "/api/v1/fraud/score-new-claim",
            json={
                "months_as_customer": 6,
                "age_of_policy_holder": 28,
                "vehicle_claim_amount": 85000,
                "injury_claim_amount": 5000,
                "property_claim_amount": 2000,
                "past_number_of_claims": 2,
                "number_of_supplements": 3,
                "police_report_filed": "NO",
                "witness_present": "NO",
                "agent_type": "External",
                "accident_area": "Urban",
                "days_policy_accident": "1 to 7",
                "day_of_week": "Saturday",
                "vehicle_category": "Sport",
            },
            timeout=10,
        )


class DashboardUser(HttpUser):
    """Simulates users loading the dashboard."""
    wait_time = between(5, 10)
    host = "http://localhost:8000"

    @task(1)
    def health(self):
        self.client.get("/health", timeout=5)

    @task(2)
    def dashboard_stats(self):
        # timeout=30 — dashboard was timing out at 10s under load before psycopg2 fix
        self.client.get("/api/v1/dashboard/stats", timeout=30)
