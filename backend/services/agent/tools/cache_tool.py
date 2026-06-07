import json
import logging
from utils.security import hash_cache_key

logger = logging.getLogger(__name__)


def _get_client():
    """
    Build a Redis client from config.settings.redis_url.
    Reading from settings (pydantic-settings) is reliable inside uvicorn
    because settings are loaded at startup. os.getenv + load_dotenv is not
    reliable inside worker processes.
    """
    try:
        from config import settings
        import redis
        url = settings.redis_url
        if not url or url == "redis://localhost:6379":
            logger.warning("REDIS_URL not configured — cache disabled")
            return None
        client = redis.from_url(
            url,
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=True,
        )
        client.ping()
        logger.info("redis_cache_connected")
        return client
    except Exception as e:
        logger.warning(f"Redis unavailable: {e} — cache disabled")
        return None


class CacheTool:
    TTL = 60 * 60 * 6  # 6 hours

    def _get(self, query: str) -> dict | None:
        client = _get_client()
        if client is None:
            return None
        try:
            key = hash_cache_key(query)
            value = client.get(key)
            if value:
                logger.info(f"cache_hit key={key[:12]}")
                return json.loads(value)
        except Exception as e:
            logger.warning(f"cache_get_error: {e}")
        return None

    def _set(self, query: str, response: dict) -> bool:
        # Poison prevention — never cache a zero-score response
        if response.get("risk_score", 0) == 0:
            logger.info("cache_write_skipped: risk_score=0 (API may have been down)")
            return False
        client = _get_client()
        if client is None:
            return False
        try:
            key = hash_cache_key(query)
            client.setex(key, self.TTL, json.dumps(response))
            logger.info(f"cache_write key={key[:12]}")
            return True
        except Exception as e:
            logger.warning(f"cache_set_error: {e}")
            return False

    def get(self, query: str) -> dict | None:
        return self._get(query)

    def set(self, query: str, response: dict) -> bool:
        return self._set(query, response)


# ── Standalone function wrappers expected by router.py ──────────────────────

_tool = CacheTool()


def get_cached_response(query: str, filters: dict = None) -> dict | None:
    """Called by agent router — checks cache before running pipeline."""
    return _tool.get(query)


def cache_response(query: str, response: dict, filters: dict = None) -> bool:
    """Called by agent router — writes result to cache after pipeline."""
    return _tool.set(query, response)