"""
Data models for the Donizo Truth Engine.

All models use Pydantic for validation and type safety.
All monetary values are in CENTS (integers only - no floating point).
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
import uuid


class EventSource(str, Enum):
    """Source type for price events."""
    HISTORIC = "HISTORIC"
    SUPPLIER = "SUPPLIER"
    HUMAN = "HUMAN"


class Outcome(str, Enum):
    """Outcome for human price events."""
    NONE = "NONE"
    QUOTE_ACCEPTED = "QUOTE_ACCEPTED"
    QUOTE_REJECTED = "QUOTE_REJECTED"


class Event(BaseModel):
    """Input event from the event stream."""
    event_id: str
    timestamp: int  # Unix timestamp in seconds
    item_id: str
    source: EventSource
    price_cents: int  # Price in cents (integer only)
    outcome: Outcome = Outcome.NONE
    meta: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('event_id')
    @classmethod
    def validate_event_id(cls, v: str) -> str:
        """Validate that event_id is a valid UUID."""
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError(f"event_id must be a valid UUID, got: {v}")
        return v

    @field_validator('price_cents')
    @classmethod
    def validate_price(cls, v: int) -> int:
        """Ensure price is non-negative."""
        if v < 0:
            raise ValueError(f"price_cents must be >= 0, got: {v}")
        return v

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: int) -> int:
        """Ensure timestamp is positive."""
        if v <= 0:
            raise ValueError(f"timestamp must be > 0, got: {v}")
        return v


class AuditLog(BaseModel):
    """Audit log entry for a processed event."""
    event_id: str
    timestamp: int
    item_id: str
    inputs_seen: Dict[str, Optional[int]]  # e.g., {"historic_cents": 1000, "supplier_cents": 1200}
    final_price_cents: int
    decision: str  # e.g., "USED_HUMAN", "USED_SUPPLIER_WITH_BIAS"
    bias_applied_cents: int
    flags: List[str] = Field(default_factory=list)
    rules_hash: str  # SHA256 hash of current state

    @field_validator('final_price_cents', 'bias_applied_cents')
    @classmethod
    def validate_price(cls, v: int) -> int:
        """Ensure price values are non-negative."""
        if v < 0:
            raise ValueError(f"price value must be >= 0, got: {v}")
        return v


class ItemState(BaseModel):
    """State for a single item."""
    bias_cents: int = 0
    last_updated_ts: int = 0
    accepted_human_deltas_cents: List[int] = Field(default_factory=list)

    @field_validator('accepted_human_deltas_cents')
    @classmethod
    def validate_deltas_length(cls, v: List[int]) -> List[int]:
        """Ensure we keep at most 5 deltas."""
        if len(v) > 5:
            return v[-5:]  # Keep last 5
        return v


class State(BaseModel):
    """Complete system state."""
    version: int = 1
    items: Dict[str, ItemState] = Field(default_factory=dict)
    state_hash: str = ""  # SHA256 hash (computed, excluded from hash calculation)

    def get_item_state(self, item_id: str) -> ItemState:
        """Get or create state for an item."""
        if item_id not in self.items:
            self.items[item_id] = ItemState()
        return self.items[item_id]
