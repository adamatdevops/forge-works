"""
Tiered config state persistence.

Hot tier:  Redis DB 1 (<5ms reads) — keyed by resource_ref
Cold tier: S3 fw-state-dev (durable, versioned) — keyed by resource_ref/version

Write path: Redis + S3 (dual write). Either failure raises — never silent.
Read path:  Redis first → S3 fallback
"""

import json
import logging

from app.config import settings
from app.dlq import RedisWriteError, S3WriteError
from app.schemas import NormalizedConfig

logger = logging.getLogger(__name__)

_redis = None


async def init_store():
    """Initialize Redis connection."""
    global _redis
    import redis.asyncio as aioredis

    if settings.redis_password:
        redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:6379/{settings.redis_db}"
    else:
        redis_url = f"redis://{settings.redis_host}:6379/{settings.redis_db}"

    _redis = aioredis.from_url(redis_url, decode_responses=True)
    logger.info("Config store initialized (Redis: %s:6379/%d, S3: %s/%s)",
                settings.redis_host, settings.redis_db, settings.s3_bucket, settings.s3_prefix)


async def close_store():
    """Close Redis connection."""
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


async def put(config: NormalizedConfig) -> None:
    """Dual write: Redis (hot) + S3 (cold). Raises on any write failure."""
    key = config.resource_ref
    # exclude_none aligns Python None with CUE "field absent" — never serialize null
    data = config.model_dump(exclude_none=True)
    data_json = json.dumps(data)

    # Hot tier — Redis
    if _redis:
        try:
            await _redis.setex(
                f"config:{key}",
                settings.redis_ttl_seconds,
                data_json,
            )
        except Exception as e:
            logger.exception("Redis write failed for %s", key)
            raise RedisWriteError(f"Redis SETEX failed for {key}: {e}") from e

    # Cold tier — S3
    try:
        import boto3
        s3 = boto3.client("s3")
        s3_key = f"{settings.s3_prefix}/{key.replace(':', '/')}/{config.schema_version}.json"
        s3.put_object(
            Bucket=settings.s3_bucket,
            Key=s3_key,
            Body=data_json.encode("utf-8"),
        )
    except Exception as e:
        logger.exception("S3 write failed for %s (Redis write may have succeeded)", key)
        raise S3WriteError(f"S3 PutObject failed for {key}: {e}") from e


async def get(resource_ref: str) -> NormalizedConfig | None:
    """Read: Redis first → S3 fallback."""
    # Hot tier
    if _redis:
        data = await _redis.get(f"config:{resource_ref}")
        if data:
            return NormalizedConfig(**json.loads(data))

    # Cold tier fallback
    try:
        import boto3
        s3 = boto3.client("s3")
        prefix = f"{settings.s3_prefix}/{resource_ref.replace(':', '/')}/"
        response = s3.list_objects_v2(
            Bucket=settings.s3_bucket, Prefix=prefix, MaxKeys=1,
        )
        contents = response.get("Contents", [])
        if not contents:
            return None

        # Get the latest version
        latest_key = sorted(contents, key=lambda x: x["Key"], reverse=True)[0]["Key"]
        obj = s3.get_object(Bucket=settings.s3_bucket, Key=latest_key)
        data = json.loads(obj["Body"].read().decode("utf-8"))

        config = NormalizedConfig(**data)

        # Promote to hot tier
        if _redis:
            await _redis.setex(
                f"config:{resource_ref}",
                settings.redis_ttl_seconds,
                json.dumps(data),
            )

        return config
    except Exception:
        logger.exception("S3 read failed for %s", resource_ref)
        return None


async def list_refs() -> list[str]:
    """List all cached resource_refs from Redis."""
    if not _redis:
        return []
    keys = []
    async for key in _redis.scan_iter(match="config:*", count=100):
        keys.append(key.replace("config:", ""))
    return keys
