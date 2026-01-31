"""Rate limiting and cost tracking for vision API calls.

This service helps manage API usage and costs for Claude's vision API:
- Per-minute request rate limiting
- Daily cost limits
- Cost tracking and reporting
- Request throttling
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class VisionRateLimiter:
    """Rate limiter and cost tracker for vision API.

    Uses in-memory storage (should use Redis in production for distributed systems).
    Tracks:
    - Requests per minute
    - Estimated costs per day
    - Request history
    """

    def __init__(
        self,
        max_requests_per_minute: int = 50,
        daily_cost_limit: float = 100.0,
        cost_per_image: float = 0.005,  # Approximate cost per image
    ):
        """Initialize rate limiter.

        Args:
            max_requests_per_minute: Maximum vision API requests per minute
            daily_cost_limit: Maximum daily cost in USD
            cost_per_image: Estimated cost per image analysis
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.daily_cost_limit = daily_cost_limit
        self.cost_per_image = cost_per_image

        # In-memory tracking (use Redis in production)
        self._request_timestamps: list[datetime] = []
        self._daily_costs: dict[str, float] = {}  # date -> total_cost
        self._request_lock = asyncio.Lock()

    async def acquire(self, estimated_cost: float | None = None) -> bool:
        """Acquire permission to make a vision API request.

        This method checks rate limits and cost limits before allowing a request.

        Args:
            estimated_cost: Estimated cost of this request (defaults to cost_per_image)

        Returns:
            True if request is allowed, False if rate limited

        Raises:
            Exception: If daily cost limit exceeded
        """
        async with self._request_lock:
            now = datetime.utcnow()
            today_str = now.date().isoformat()
            estimated_cost = estimated_cost or self.cost_per_image

            # Check daily cost limit
            today_cost = self._daily_costs.get(today_str, 0.0)
            if today_cost + estimated_cost > self.daily_cost_limit:
                logger.error(
                    f"Daily cost limit exceeded: ${today_cost:.2f} + ${estimated_cost:.2f} "
                    f"> ${self.daily_cost_limit:.2f}"
                )
                raise Exception(
                    f"Daily cost limit exceeded: ${today_cost:.2f} of ${self.daily_cost_limit:.2f}"
                )

            # Clean up old request timestamps (older than 1 minute)
            cutoff = now - timedelta(minutes=1)
            self._request_timestamps = [ts for ts in self._request_timestamps if ts > cutoff]

            # Check rate limit
            if len(self._request_timestamps) >= self.max_requests_per_minute:
                logger.warning(
                    f"Rate limit hit: {len(self._request_timestamps)} requests in last minute "
                    f"(limit: {self.max_requests_per_minute})"
                )
                return False

            # Record request
            self._request_timestamps.append(now)
            self._daily_costs[today_str] = today_cost + estimated_cost

            logger.debug(
                f"Vision API request approved: "
                f"{len(self._request_timestamps)}/{self.max_requests_per_minute} per minute, "
                f"${self._daily_costs[today_str]:.2f}/${self.daily_cost_limit:.2f} daily cost"
            )

            return True

    async def wait_for_capacity(
        self, estimated_cost: float | None = None, max_wait_seconds: int = 60
    ) -> None:
        """Wait until capacity is available (with timeout).

        Args:
            estimated_cost: Estimated cost of request
            max_wait_seconds: Maximum seconds to wait

        Raises:
            TimeoutError: If capacity not available within max_wait_seconds
            Exception: If daily cost limit exceeded
        """
        start_time = datetime.utcnow()

        while True:
            if await self.acquire(estimated_cost):
                return

            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed >= max_wait_seconds:
                raise TimeoutError(
                    f"Rate limit timeout after {max_wait_seconds}s waiting for capacity"
                )

            # Wait before retry (exponential backoff)
            wait_time = min(2 ** int(elapsed / 5), 10)  # Max 10 seconds
            logger.info(f"Rate limited, waiting {wait_time}s before retry...")
            await asyncio.sleep(wait_time)

    async def record_actual_cost(self, actual_cost: float) -> None:
        """Record actual cost after API response (to adjust estimates).

        Args:
            actual_cost: Actual cost from API response
        """
        async with self._request_lock:
            today_str = datetime.utcnow().date().isoformat()

            # Adjust daily cost (may have estimated wrong)
            current = self._daily_costs.get(today_str, 0.0)

            # Subtract one estimated cost and add actual cost
            adjusted = current - self.cost_per_image + actual_cost
            self._daily_costs[today_str] = max(0, adjusted)

            logger.debug(f"Adjusted daily cost: ${current:.4f} -> ${adjusted:.4f}")

    def get_current_stats(self) -> dict[str, Any]:
        """Get current rate limiting and cost stats.

        Returns:
            dict with current usage statistics
        """
        now = datetime.utcnow()
        today_str = now.date().isoformat()

        # Clean old timestamps
        cutoff = now - timedelta(minutes=1)
        recent_requests = [ts for ts in self._request_timestamps if ts > cutoff]

        return {
            "requests_last_minute": len(recent_requests),
            "max_requests_per_minute": self.max_requests_per_minute,
            "capacity_remaining": max(0, self.max_requests_per_minute - len(recent_requests)),
            "daily_cost": self._daily_costs.get(today_str, 0.0),
            "daily_cost_limit": self.daily_cost_limit,
            "cost_remaining": max(0, self.daily_cost_limit - self._daily_costs.get(today_str, 0.0)),
            "estimated_cost_per_request": self.cost_per_image,
        }

    def reset_daily_costs(self, date: str | None = None) -> None:
        """Reset daily costs (for testing or manual override).

        Args:
            date: Date to reset (YYYY-MM-DD), or None for today
        """
        date_str = date or datetime.utcnow().date().isoformat()
        if date_str in self._daily_costs:
            del self._daily_costs[date_str]
            logger.info(f"Reset daily costs for {date_str}")


# Global instance (in production, use Redis-backed implementation)
_global_rate_limiter: VisionRateLimiter | None = None


def get_vision_rate_limiter(
    max_requests_per_minute: int = 50,
    daily_cost_limit: float = 100.0,
    cost_per_image: float = 0.005,
) -> VisionRateLimiter:
    """Get or create the global vision rate limiter.

    Args:
        max_requests_per_minute: Max requests per minute
        daily_cost_limit: Max daily cost in USD
        cost_per_image: Estimated cost per image

    Returns:
        VisionRateLimiter instance
    """
    global _global_rate_limiter

    if _global_rate_limiter is None:
        _global_rate_limiter = VisionRateLimiter(
            max_requests_per_minute=max_requests_per_minute,
            daily_cost_limit=daily_cost_limit,
            cost_per_image=cost_per_image,
        )

    return _global_rate_limiter


class RedisVisionRateLimiter(VisionRateLimiter):
    """Redis-backed rate limiter for distributed systems.

    This is a placeholder for production implementation using Redis.
    Provides the same interface as VisionRateLimiter but with distributed state.
    """

    def __init__(self, redis_url: str, **kwargs):
        """Initialize Redis-backed rate limiter.

        Args:
            redis_url: Redis connection URL
            **kwargs: Passed to VisionRateLimiter
        """
        super().__init__(**kwargs)
        self.redis_url = redis_url

        # TODO: Initialize Redis client
        # from redis.asyncio import Redis
        # self.redis = Redis.from_url(redis_url)

        logger.warning("RedisVisionRateLimiter not fully implemented, using in-memory fallback")

    # TODO: Override acquire(), record_actual_cost(), etc. to use Redis
    # Use Redis keys like:
    # - "vision:requests:{minute}" -> set of timestamps
    # - "vision:cost:{date}" -> float
    # - Use INCR, EXPIRE, GET, SET commands
