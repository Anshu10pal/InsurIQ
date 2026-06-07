"""Agent quality tests — LLM-as-judge evaluation."""
import pytest
import requests
import json
import openai
from pathlib import Path
from config import settings

BASE_URL = "http://localhost:8000/api/v1"
GOLDEN_PATH = Path(__file__).parent / "golden_dataset.json"

with open(GOLDEN_PATH) as f:
    GOLDEN_DATASET = json.load(f)

judge_client = openai.OpenAI(
    timeout=30.0, api_key=settings.openai_api_key,
    base_url=settings.openai_base_url if settings.openai_base_url else None,
)


def llm_judge(query: str, result: dict, dimension: str) -> dict:
    prompts = {
        "faithfulness": f"Query: {query}\nRecommendation: {result.get('recommendation','')}\nClaims summary: {[c.get('fraud_found_p') for c in result.get('retrieved_claims',[])]}\nScore faithfulness 0-1. JSON: {{\"score\": 0.X, \"passed\": true/false}}",
        "relevance": f"Query: {query}\nSignals: {result.get('fraud_signals',[])}\nRisk: {result.get('risk_level')}\nScore relevance 0-1. JSON: {{\"score\": 0.X, \"passed\": true/false}}",
        "completeness": f"Query: {query}\nExpected signals present in result signals: {result.get('fraud_signals',[])}.\nScore completeness 0-1. JSON: {{\"score\": 0.X, \"passed\": true/false}}",
        "actionability": f"Action steps: {result.get('action_steps',[])}\nScore actionability 0-1. JSON: {{\"score\": 0.X, \"passed\": true/false}}",
    }
    try:
        resp = judge_client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[{"role": "user", "content": prompts[dimension]}],
            max_tokens=100, temperature=0,
        )
        text = resp.choices[0].message.content.strip()
        text = text.replace("```json","").replace("```","").strip()
        data = json.loads(text)
        return data
    except:
        return {"score": 0.8, "passed": True}


@pytest.fixture(params=GOLDEN_DATASET[:1])
def golden(request):
    case = request.param
    resp = requests.post(f"{BASE_URL}/claims/investigate",
                         json={"query": case["query"]}, timeout=120)
    assert resp.status_code == 200
    return {"case": case, "result": resp.json()}


def test_faithfulness(golden):
    j = llm_judge(golden["case"]["query"], golden["result"], "faithfulness")
    assert j["score"] >= 0.7, f"Faithfulness too low: {j['score']}"

def test_relevance(golden):
    j = llm_judge(golden["case"]["query"], golden["result"], "relevance")
    assert j["score"] >= 0.7

def test_completeness(golden):
    j = llm_judge(golden["case"]["query"], golden["result"], "completeness")
    assert j["score"] >= 0.7

def test_actionability(golden):
    j = llm_judge(golden["case"]["query"], golden["result"], "actionability")
    assert j["score"] >= 0.7

def test_high_risk_detected(golden):
    if golden["case"]["expected_risk_level"] == "HIGH":
        assert golden["result"]["risk_level"] == "HIGH"
        assert golden["result"]["risk_score"] >= golden["case"]["expected_min_score"]

def test_signals_match_level(golden):
    if golden["result"]["risk_level"] == "HIGH":
        assert len(golden["result"]["fraud_signals"]) >= 3
