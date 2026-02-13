from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


def _get_storage_uri() -> str:
    """Use Redis for rate limiting if available, else fall back to memory."""
    if settings.redis_url and settings.redis_url != "memory://":
        try:
            import redis

            r = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1)
            r.ping()
            return settings.redis_url
        except Exception:
            return "memory://"
    return "memory://"


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_get_storage_uri(),
    default_limits=["100/minute"],
)

# Rate limit constants
CHAT_RATE_LIMIT = "20/minute"
EXPORT_RATE_LIMIT = "5/hour"
