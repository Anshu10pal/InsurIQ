"""Agent 4 — recommendation agent using GPT-4o-mini."""
import openai
from services.agent.graph.state import ClaimInvestigationState
from config import settings
from utils.logging import get_logger

logger = get_logger(__name__)

client = openai.OpenAI(
    timeout=30.0,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url if settings.openai_base_url else None,
)

TEMPLATE = """You are an insurance fraud analyst. Provide a concise recommendation.

Query: {query}
Risk Score: {score}/100 ({level})
Signals: {signals}
Policy Issues: {issues}

Write 2-3 sentences of recommendation and 4 specific action steps.
Format: RECOMMENDATION: [text] ACTIONS: 1.[step] 2.[step] 3.[step] 4.[step]"""


def recommendation_agent(state: ClaimInvestigationState) -> ClaimInvestigationState:
    logger.info("recommendation_agent_started")
    state["current_agent"] = "recommendation"
    try:
        query = state.get("query", "")
        score = state.get("fraud_score", 0)
        level = state.get("risk_level", "LOW")
        signals = state.get("fraud_signals", [])[:6]
        issues = state.get("policy_issues", [])[:3]

        prompt = TEMPLATE.format(
            query=query[:200], score=score, level=level,
            signals=", ".join(signals) or "None",
            issues=", ".join(issues) or "None",
        )

        try:
            response = client.chat.completions.create(
                model=settings.openai_chat_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.openai_max_tokens,
                temperature=0.3,
            )
            text = response.choices[0].message.content.strip()
            rec, actions = _parse_response(text, signals, score, level)
            confidence = 0.95
        except Exception as e:
            logger.warning("llm_failed_using_template", error=str(e))
            rec, actions = _template_response(signals, score, level)
            confidence = 0.5

        state["recommendation"] = rec
        state["action_steps"] = actions
        state["confidence"] = confidence
        state["completed_agents"] = state.get("completed_agents", []) + ["recommendation"]
        logger.info("recommendation_agent_complete", confidence=confidence)
    except Exception as e:
        logger.error("recommendation_agent_failed", error=str(e))
        state["recommendation"] = "Investigation recommended based on detected fraud signals."
        state["action_steps"] = ["Review claim documentation", "Interview policyholder"]
        state["confidence"] = 0.5
    return state


def _parse_response(text: str, signals: list, score: int, level: str):
    lines = text.split("\n")
    rec = ""
    actions = []
    for line in lines:
        line = line.strip()
        if line.startswith("RECOMMENDATION:"):
            rec = line.replace("RECOMMENDATION:", "").strip()
        elif line.startswith(("1.", "2.", "3.", "4.", "5.")):
            actions.append(line[2:].strip())
    if not rec:
        rec = text[:300]
    if not actions:
        actions = _template_response(signals, score, level)[1]
    return rec, actions[:5]


def _template_response(signals: list, score: int, level: str):
    rec = f"The claim presents a {level.lower()} fraud risk (score {score}/100) with {len(signals)} active signals. Further investigation is recommended."
    actions = [
        "Review all claim documentation for inconsistencies.",
        "Interview the policyholder about the incident timeline.",
        "Verify repair estimates with an independent assessor.",
        "Check policyholder claims history for patterns.",
    ]
    return rec, actions
