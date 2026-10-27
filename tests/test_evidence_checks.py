from evidence_checks import check_draft_against_evidence


def test_rejects_unsupported_numeric_claim():
    ok, reason = check_draft_against_evidence(
        "The protocol moved 4.2 million USDC in one transaction.",
        "The protocol moved funds in one transaction.",
    )
    assert not ok
    assert reason == "unsupported_numeric_claim"


def test_rejects_unsupported_wallet_address():
    ok, reason = check_draft_against_evidence(
        "Funds moved from 0x1234567890abcdef.",
        "The incident involved a protocol contract.",
    )
    assert not ok
    assert reason == "unsupported_address"


def test_accepts_numbers_and_addresses_present_in_source():
    evidence = "The incident moved 4.2 million USDC from 0x1234567890abcdef."
    ok, reason = check_draft_against_evidence(
        "The incident moved 4.2 million USDC from 0x1234567890abcdef.",
        evidence,
    )
    assert ok
    assert reason == "supported_literals"


def test_ignores_numbered_howto_steps_and_source_urls():
    ok, reason = check_draft_against_evidence(
        "1. Open the explorer. 2. Search for the transaction. Source: https://example.com/123456",
        "Use a block explorer to search for a transaction.",
    )
    assert ok
    assert reason == "supported_literals"
