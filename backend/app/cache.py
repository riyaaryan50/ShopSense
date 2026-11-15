"""Recommendation cache (sprint plan: key ``user:{id}:recs``, 1-hour TTL).

Uses Redis when REDIS_URL is set and reachable, otherwise a per-process
in-memory cache, so local development needs no Redis server. Entries are
invalidated whenever the user does something that should change their
recommendations (cart, wishlist, interaction or survey changes).
"""

import json
import logging
import os
import threading
import time

log = logging.getLogger(__name__)

TTL_SECONDS = int(os.getenv("RECS_CACHE_TTL", "3600"))


class _MemoryCache:
    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            expires, value = item
            if expires < time.time():
                self._data.pop(key, None)
                return None
            return value

    def setex(self, key, ttl, value):
        with self._lock:
            self._data[key] = (time.time() + ttl, value)

    def delete(self, key):
        with self._lock:
            self._data.pop(key, None)


def _connect():
    url = os.getenv("REDIS_URL")
    if url:
        try:
            import redis
            client = redis.Redis.from_url(url, socket_timeout=1, socket_connect_timeout=1)
            client.ping()
            log.info("Recommendation cache: Redis")
            return client, "redis"
        except Exception as error:  # noqa: BLE001 - fall back to memory
            log.warning("Redis unavailable (%s); using in-memory cache", error)
    return _MemoryCache(), "memory"


_backend, BACKEND = _connect()


def recs_key(user_id):
    return f"user:{int(user_id)}:recs"


def get_recs(user_id):
    try:
        raw = _backend.get(recs_key(user_id))
        return json.loads(raw) if raw else None
    except Exception as error:  # noqa: BLE001 - a cache failure must never break a request
        log.warning("cache read failed: %s", error)
        return None


def set_recs(user_id, payload):
    try:
        _backend.setex(recs_key(user_id), TTL_SECONDS, json.dumps(payload))
    except Exception as error:  # noqa: BLE001
        log.warning("cache write failed: %s", error)


def invalidate_recs(user_id):
    try:
        _backend.delete(recs_key(user_id))
    except Exception as error:  # noqa: BLE001
        log.warning("cache delete failed: %s", error)
