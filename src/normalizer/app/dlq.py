"""
Dead-letter queue support for the normalizer.

A failed message must be published to the DLQ topic (with structured error
context) before the consumer offset advances — otherwise we silently lose it.

Error codes (single source of truth):
  FW-NL-PARSE-001  Event JSON failed to decode / required fields missing
  FW-NL-NORM-001   A normalizer raised while processing a valid event
  FW-NL-S3-001     Cold-tier (S3) write failed after Redis succeeded
  FW-NL-REDIS-001  Hot-tier (Redis) write failed
  FW-NL-SRC-001    Event source did not match the pod's expected source
"""

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field

# Error code constants — keep in sync with the docstring above.
FW_NL_PARSE_001 = "FW-NL-PARSE-001"
FW_NL_NORM_001 = "FW-NL-NORM-001"
FW_NL_S3_001 = "FW-NL-S3-001"
FW_NL_REDIS_001 = "FW-NL-REDIS-001"
FW_NL_SRC_001 = "FW-NL-SRC-001"


class DLQEvent(BaseModel):
    """Dead-letter queue envelope. Shape mirrors webhook-gateway's DLQEvent."""

    event_id: str = Field(default_factory=lambda: f"dlq_{uuid.uuid4().hex[:12]}")
    correlation_id: str = ""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source: str
    error_code: str
    error_message: str
    original_payload: dict = Field(default_factory=dict)
    headers: dict = Field(default_factory=dict)


class S3WriteError(Exception):
    """Cold-tier write failed."""


class RedisWriteError(Exception):
    """Hot-tier write failed."""
