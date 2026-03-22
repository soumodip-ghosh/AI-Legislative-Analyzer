import hashlib
import json
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# In-memory cache. For production, replace with Redis or a simple SQLite store.
_cache: dict[str, dict] = {}
CACHE_TTL = 60 * 60 * 6  # 6 hours — long enough to be useful, short enough not to serve stale law


def document_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def get_cached_result(content_hash: str) -> Optional[dict]:
    entry = _cache.get(content_hash)
    if not entry:
        return None

    if time.time() - entry["cached_at"] > CACHE_TTL:
        del _cache[content_hash]
        logger.info(f"Cache expired for {content_hash[:8]}...")
        return None

    logger.info(f"Cache hit for {content_hash[:8]}...")
    return entry["result"]


def set_cached_result(content_hash: str, result: dict) -> None:
    _cache[content_hash] = {
        "result": result,
        "cached_at": time.time(),
    }
    logger.info(f"Cached result for {content_hash[:8]}... ({len(_cache)} entries total)")


def cache_stats() -> dict:
    return {
        "entries": len(_cache),
        "oldest_age_seconds": min(
            (time.time() - v["cached_at"] for v in _cache.values()), default=0
        ),
    }
