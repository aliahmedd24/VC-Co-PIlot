"""Vision analysis caching service.

Caches vision analysis results to avoid redundant API calls for the same images.
Uses Redis with 7-day TTL by default.
"""

import hashlib
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class VisionCache:
    """Cache for vision analysis results.

    Uses image content hash as cache key to detect duplicate images.
    Stores analysis results with TTL to avoid stale data.
    """

    def __init__(self, redis_url: str | None = None, ttl_days: int = 7):
        """Initialize vision cache.

        Args:
            redis_url: Redis connection URL (None = in-memory cache)
            ttl_days: Time-to-live for cached entries in days
        """
        self.ttl_days = ttl_days
        self.ttl_seconds = ttl_days * 24 * 60 * 60

        # In-memory cache (for development/testing)
        self._cache: dict[str, Any] = {}

        # Redis cache (for production)
        self.redis_client = None
        if redis_url:
            try:
                # Lazy import to avoid dependency issues
                import redis.asyncio as redis

                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                logger.info(f"Vision cache initialized with Redis (TTL: {ttl_days} days)")
            except ImportError:
                logger.warning(
                    "redis package not installed, using in-memory cache. "
                    "Install with: pip install redis"
                )
        else:
            logger.info(f"Vision cache initialized in-memory (TTL: {ttl_days} days)")

    def _compute_image_hash(self, image_data: bytes) -> str:
        """Compute SHA256 hash of image data.

        Args:
            image_data: Image bytes

        Returns:
            Hex-encoded hash string
        """
        return hashlib.sha256(image_data).hexdigest()

    def _make_cache_key(
        self, image_hash: str, analysis_type: str, prompt_hash: str | None = None
    ) -> str:
        """Create cache key from image hash and analysis type.

        Args:
            image_hash: Hash of image content
            analysis_type: Type of analysis
            prompt_hash: Optional hash of custom prompt

        Returns:
            Cache key string
        """
        if prompt_hash:
            return f"vision:{analysis_type}:{image_hash}:{prompt_hash}"
        return f"vision:{analysis_type}:{image_hash}"

    async def get(
        self, image_data: bytes, analysis_type: str, custom_prompt: str | None = None
    ) -> dict[str, Any] | None:
        """Get cached vision analysis result.

        Args:
            image_data: Image bytes
            analysis_type: Type of analysis
            custom_prompt: Optional custom prompt (for cache key)

        Returns:
            Cached result dict or None if not found
        """
        # Compute hashes
        image_hash = self._compute_image_hash(image_data)
        prompt_hash = hashlib.sha256(custom_prompt.encode()).hexdigest() if custom_prompt else None
        cache_key = self._make_cache_key(image_hash, analysis_type, prompt_hash)

        # Try Redis first
        if self.redis_client:
            try:
                cached_json = await self.redis_client.get(cache_key)
                if cached_json:
                    logger.info(f"Vision cache HIT (Redis): {cache_key}")
                    return json.loads(cached_json)
            except Exception as e:
                logger.warning(f"Redis cache read failed: {str(e)}")

        # Fallback to in-memory
        if cache_key in self._cache:
            logger.info(f"Vision cache HIT (memory): {cache_key}")
            return self._cache[cache_key]

        logger.debug(f"Vision cache MISS: {cache_key}")
        return None

    async def set(
        self,
        image_data: bytes,
        analysis_type: str,
        result: dict[str, Any],
        custom_prompt: str | None = None,
    ) -> None:
        """Store vision analysis result in cache.

        Args:
            image_data: Image bytes
            analysis_type: Type of analysis
            result: Analysis result to cache
            custom_prompt: Optional custom prompt
        """
        # Compute hashes
        image_hash = self._compute_image_hash(image_data)
        prompt_hash = hashlib.sha256(custom_prompt.encode()).hexdigest() if custom_prompt else None
        cache_key = self._make_cache_key(image_hash, analysis_type, prompt_hash)

        # Store in Redis
        if self.redis_client:
            try:
                result_json = json.dumps(result)
                await self.redis_client.setex(cache_key, self.ttl_seconds, result_json)
                logger.info(f"Vision cache SET (Redis): {cache_key}")
            except Exception as e:
                logger.warning(f"Redis cache write failed: {str(e)}")

        # Also store in memory
        self._cache[cache_key] = result
        logger.debug(f"Vision cache SET (memory): {cache_key}")

    async def invalidate(
        self, image_data: bytes, analysis_type: str, custom_prompt: str | None = None
    ) -> None:
        """Invalidate cached result.

        Args:
            image_data: Image bytes
            analysis_type: Type of analysis
            custom_prompt: Optional custom prompt
        """
        image_hash = self._compute_image_hash(image_data)
        prompt_hash = hashlib.sha256(custom_prompt.encode()).hexdigest() if custom_prompt else None
        cache_key = self._make_cache_key(image_hash, analysis_type, prompt_hash)

        # Delete from Redis
        if self.redis_client:
            try:
                await self.redis_client.delete(cache_key)
            except Exception as e:
                logger.warning(f"Redis cache delete failed: {str(e)}")

        # Delete from memory
        if cache_key in self._cache:
            del self._cache[cache_key]

        logger.info(f"Vision cache INVALIDATE: {cache_key}")

    async def clear_all(self) -> None:
        """Clear all vision cache entries."""
        # Clear Redis (delete keys matching pattern)
        if self.redis_client:
            try:
                # Scan for all vision:* keys
                cursor = 0
                while True:
                    cursor, keys = await self.redis_client.scan(
                        cursor, match="vision:*", count=100
                    )
                    if keys:
                        await self.redis_client.delete(*keys)
                    if cursor == 0:
                        break
                logger.info("Cleared all vision cache entries from Redis")
            except Exception as e:
                logger.warning(f"Redis cache clear failed: {str(e)}")

        # Clear memory
        self._cache.clear()
        logger.info("Cleared all vision cache entries from memory")

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            dict with cache stats
        """
        stats = {
            "backend": "redis" if self.redis_client else "memory",
            "ttl_days": self.ttl_days,
            "memory_entries": len(self._cache),
        }

        # Get Redis stats
        if self.redis_client:
            try:
                # Count keys matching pattern
                cursor = 0
                redis_count = 0
                while True:
                    cursor, keys = await self.redis_client.scan(
                        cursor, match="vision:*", count=100
                    )
                    redis_count += len(keys)
                    if cursor == 0:
                        break

                stats["redis_entries"] = redis_count

                # Get Redis info
                info = await self.redis_client.info("memory")
                stats["redis_memory_used_mb"] = info.get("used_memory", 0) / (1024 * 1024)

            except Exception as e:
                logger.warning(f"Failed to get Redis stats: {str(e)}")
                stats["redis_error"] = str(e)

        return stats

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()


# Global instance
_global_vision_cache: VisionCache | None = None


def get_vision_cache(redis_url: str | None = None, ttl_days: int = 7) -> VisionCache:
    """Get or create the global vision cache.

    Args:
        redis_url: Redis connection URL
        ttl_days: Time-to-live in days

    Returns:
        VisionCache instance
    """
    global _global_vision_cache

    if _global_vision_cache is None:
        _global_vision_cache = VisionCache(redis_url=redis_url, ttl_days=ttl_days)

    return _global_vision_cache
