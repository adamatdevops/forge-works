import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    """Normalized event envelope published to Kafka.

    @schema: schemas/event-envelope.schema.json
    """

    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    correlation_id: str = ""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source: str
    type: str
    metadata: dict = Field(default_factory=dict)
    payload: dict = Field(default_factory=dict)


class DLQEvent(BaseModel):
    """Dead-letter queue envelope with error context."""

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
