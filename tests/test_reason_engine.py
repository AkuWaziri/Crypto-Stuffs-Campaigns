from datetime import datetime, timezone

from models import ActivityEvent
from reason_engine import explain_event


def test_transaction_reason_is_confirmed():
    event = ActivityEvent("wallet", "WHALE_WALLET", "TOKEN", "BUY", 1000, "solana", datetime.now(timezone.utc), "helius", "sig", ())
    explanation = explain_event(event)
    assert explanation.status == "CONFIRMED"
    assert explanation.confidence == "HIGH"


def test_unknown_reason_stays_unknown():
    event = ActivityEvent("wallet", "WHALE_WALLET", "TOKEN", "UNKNOWN", None, "solana", datetime.now(timezone.utc), "provider")
    explanation = explain_event(event)
    assert explanation.status == "UNKNOWN"
