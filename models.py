from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

Action = Literal["BUY", "SELL", "TRANSFER", "UNKNOWN"]
Confidence = Literal["HIGH", "MEDIUM", "LOW"]
ReasonStatus = Literal["CONFIRMED", "INFERRED", "UNKNOWN"]

@dataclass(frozen=True)
class ActivityEvent:
    entity: str
    entity_type: str
    asset: str
    action: Action
    value_usd: float | None
    chain: str | None
    timestamp: datetime
    source: str
    tx_or_reference: str | None = None
    evidence: tuple[str, ...] = field(default_factory=tuple)

@dataclass(frozen=True)
class Explanation:
    status: ReasonStatus
    reason: str
    evidence: tuple[str, ...] = field(default_factory=tuple)
    confidence: Confidence = "LOW"


def classify_crypto_flow(*, received_target: bool, spent_target: bool, is_swap: bool) -> Action:
    """Classify the tracked asset, not the transaction as a whole."""
    if not is_swap:
        return "TRANSFER"
    if received_target and not spent_target:
        return "BUY"
    if spent_target and not received_target:
        return "SELL"
    return "UNKNOWN"
