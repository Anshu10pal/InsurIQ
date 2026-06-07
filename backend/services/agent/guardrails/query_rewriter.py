"""HyDE query rewriter — rewrites query to dataset vocabulary."""
import openai
from config import settings
from utils.logging import get_logger

logger = get_logger(__name__)

client = openai.OpenAI(
    timeout=20.0,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url if settings.openai_base_url else None,
)

SYSTEM_PROMPT = """You are an insurance fraud analysis assistant.
Rewrite the query using these exact field values from the fraud dataset:
AccidentArea: Urban/Rural | PoliceReportFiled: Yes/No | WitnessPresent: Yes/No
AgentType: External/Internal | Days_Policy_Accident: none/1 to 7/8 to 15/15 to 30/more than 30
PastNumberOfClaims: none/1/2 to 4/more than 4 | NumberOfSupplements: none/1 to 2/3 to 5/more than 5
VehiclePrice: less than 20000/20000 to 29000/30000 to 39000/40000 to 59000/60000 to 69000/more than 69000
Keep it concise under 100 words."""


def rewrite_query(query: str) -> str:
    try:
        response = client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": query}],
            max_tokens=150, temperature=0.1,
        )
        rewritten = response.choices[0].message.content.strip()
        logger.info("query_rewritten", original_len=len(query), rewritten_len=len(rewritten))
        return rewritten
    except Exception as e:
        logger.warning("query_rewrite_failed", error=str(e))
        return query
