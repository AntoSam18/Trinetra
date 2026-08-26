import json

import redis

from common_gateway_service.core.config import settings


def _client() -> redis.Redis | None:
    if not settings.redis_url:
        return None
    return redis.Redis.from_url(
        settings.redis_url,
        socket_connect_timeout=settings.redis_connect_timeout_seconds,
        socket_timeout=settings.redis_socket_timeout_seconds,
        decode_responses=True,
    )


def cache_get_json(key: str) -> object | None:
    client = _client()
    if client is None:
        return None
    value = client.get(key)
    if not value:
        return None
    try:
        return json.loads(value)
    except Exception:
        return None


def cache_set_json(key: str, value: object, ttl_seconds: int | None = None) -> None:
    client = _client()
    if client is None:
        return
    payload = json.dumps(value)
    ttl = ttl_seconds if ttl_seconds is not None else settings.redis_default_ttl_seconds
    client.set(key, payload, ex=ttl)


def cache_delete_prefix(prefix: str) -> int:
    client = _client()
    if client is None:
        return 0
    deleted = 0
    cursor = 0
    while True:
        cursor, keys = client.scan(cursor=cursor, match=f"{prefix}*")
        if keys:
            deleted += client.delete(*keys)
        if cursor == 0:
            break
    return int(deleted)

