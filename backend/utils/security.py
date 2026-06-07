import hashlib


def hash_cache_key(query: str) -> str:
    """
    Deterministic SHA-256 cache key from a query string.
    Normalised: lowercased + stripped before hashing so minor
    whitespace/case differences hit the same cache entry.
    """
    normalised = query.strip().lower()
    return "insuriq:inv:" + hashlib.sha256(normalised.encode("utf-8")).hexdigest()
