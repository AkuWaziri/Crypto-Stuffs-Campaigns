from datetime import datetime, timezone

from models import FreshSignal, Narrative
from qualification import qualify_with_verification
from solana_verifier import VerificationResult
from sources import SOURCE_ACCOUNTS


def make_narrative():
    signal = FreshSignal(SOURCE_ACCOUNTS[0], "1", "DOGE payments", "https://x.test/1", datetime.now(timezone.utc))
    return Narrative("n1", "DOGE payments", [signal], 95, 95, 95, 95)


def test_qualified_after_clean_verification():
    result = qualify_with_verification(make_narrative(), VerificationResult("n1", (), 0, False, 0))
    assert result.qualified is True


def test_saturated_narrative_rejected():
    verification = VerificationResult("n1", (), 50, True, 100)
    result = qualify_with_verification(make_narrative(), verification)
    assert result.qualified is False
