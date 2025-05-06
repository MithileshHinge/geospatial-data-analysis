from typing import Callable, TypeVar, cast

import redis
import orjson

from .settings import settings

T = TypeVar("T")

__all__ = ["Cache", "get_cache"]

JSON_dumps = orjson.dumps
JSON_loads = orjson.loads


class Cache:
    """
    Sync Redis wrapper with handy get_or_set(write_through) semantics.
    """

    def __init__(self):
        self.r = redis.Redis.from_url(settings.url, decode_responses=False)

    # low-level helpers
    def get_raw(self, key: str) -> bytes | None:
        return cast(bytes | None, self.r.get(key))

    def set_raw(self, key: str, value: bytes, ttl: int) -> None:
        self.r.setex(key, ttl, value)

    # high-level JSON helpers
    def get_json(self, key: str) -> T | None:
        data = self.r.get(key)
        if data is None:
            return None

        # Redis returns bytes, which is what orjson.loads expects
        return JSON_loads(data)  # type: ignore

    def set_json(self, key: str, value: T, ttl: int) -> None:
        self.r.setex(key, ttl, JSON_dumps(value))

    # simple get/set convenience methods
    def get(self, key: str) -> T | None:
        """
        Get a value from cache. Returns None if key doesn't exist.
        """
        return self.get_json(key)

    def set(self, key: str, value: T, ttl: int) -> None:
        """
        Set a value in cache with the specified TTL in seconds.
        """
        self.set_json(key, value, ttl)

    # read-through / write-through
    def get_or_set(
        self,
        key: str,
        ttl: int,
        compute: Callable[[], T],
    ) -> T:
        cached = self.get_json(key)
        if cached is not None:
            return cached
        value = compute()
        # assume `value` is JSON-serialisable
        self.set_json(key, value, ttl)
        return value


_cache_singleton: Cache | None = None


def get_cache(url: str | None = None) -> Cache:
    global _cache_singleton
    if _cache_singleton is None:
        _cache_singleton = Cache()
    return _cache_singleton
