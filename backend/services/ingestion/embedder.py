"""
Embedder — generates OpenAI text-embedding-3-small vectors.
Redis embedding cache disabled during ingestion for reliability.
"""
from typing import List
import openai
from config import settings
from utils.logging import get_logger
from utils.resilience import retry_openai

logger = get_logger(__name__)

REDIS_AVAILABLE = False
redis_conn = None

client = openai.OpenAI(
    timeout=30.0,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url if settings.openai_base_url else None,
)


@retry_openai
def _call_openai_embeddings(texts: List[str]) -> List[List[float]]:
    response = client.embeddings.create(input=texts, model=settings.openai_embedding_model)
    return [item.embedding for item in response.data]


def generate_embeddings(narratives: List[str]) -> List[List[float]]:
    embeddings = []
    batch_size = settings.openai_embedding_batch_size
    total_batches = (len(narratives) + batch_size - 1) // batch_size
    logger.info("embedding_cache_check", total=len(narratives), cache_hits=0, api_calls_needed=len(narratives))
    for batch_start in range(0, len(narratives), batch_size):
        batch = narratives[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        logger.info("embedding_batch", batch=batch_num, total_batches=total_batches, batch_size=len(batch))
        batch_embeddings = _call_openai_embeddings(batch)
        embeddings.extend(batch_embeddings)
    logger.info("embeddings_generated", total=len(embeddings))
    return embeddings


def generate_single_embedding(text: str) -> List[float]:
    embeddings = _call_openai_embeddings([text])
    return embeddings[0]
