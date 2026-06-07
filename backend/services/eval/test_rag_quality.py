"""RAG quality tests — structural validation of pipeline outputs."""
import pytest
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"
GOLDEN_PATH = Path(__file__).parent / "golden_dataset.json"

with open(GOLDEN_PATH) as f:
    GOLDEN_DATASET = json.load(f)


@pytest.fixture(params=GOLDEN_DATASET[:1])
def golden(request):
    case = request.param
    resp = requests.post(f"{BASE_URL}/claims/investigate",
                         json={"query": case["query"], "use_query_rewriting": False}, timeout=120)
    assert resp.status_code == 200, f"API failed: {resp.text}"
    return {"case": case, "result": resp.json()}


def test_minimum_retrieval_count(golden):
    assert len(golden["result"]["retrieved_claims"]) >= 3

def test_risk_score_range(golden):
    assert 0 <= golden["result"]["risk_score"] <= 100

def test_risk_level_valid(golden):
    assert golden["result"]["risk_level"] in ["HIGH", "MEDIUM", "LOW"]

def test_fraud_signals_present(golden):
    if golden["case"]["expected_risk_level"] == "HIGH":
        assert len(golden["result"]["fraud_signals"]) > 0

def test_recommendation_not_empty(golden):
    rec = golden["result"]["recommendation"]
    assert rec is not None and len(rec) > 20

def test_action_steps_present(golden):
    assert len(golden["result"]["action_steps"]) >= 1

def test_retrieved_claims_have_fields(golden):
    for claim in golden["result"]["retrieved_claims"]:
        assert "policy_number" in claim
        assert "fraud_risk_score" in claim
        assert "fraud_found_p" in claim

def test_confidence_range(golden):
    assert 0.0 <= golden["result"]["confidence"] <= 1.0

def test_policy_issues_list(golden):
    assert isinstance(golden["result"]["policy_issues"], list)

def test_response_schema(golden):
    required = ["risk_score","risk_level","fraud_signals","retrieved_claims",
                "recommendation","confidence","action_steps","trace_id"]
    for key in required:
        assert key in golden["result"], f"Missing key: {key}"
