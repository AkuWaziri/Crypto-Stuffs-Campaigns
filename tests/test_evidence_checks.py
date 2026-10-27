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


def test_editorial_holds_draft_with_unsupported_number(monkeypatch, capsys):
    from types import SimpleNamespace
    import editorial

    completions = SimpleNamespace(
        create=lambda **kwargs: SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(
                content="The protocol moved 4.2 million USDC during the exploit."
            ))]
        )
    )
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    monkeypatch.setattr(editorial, "_client", lambda: fake_client)
    monkeypatch.setattr(editorial, "_fetch_article_text", lambda url: "")
    item = {
        "id": "unsupported-number",
        "source": "medium",
        "text": "A protocol exploit affected a lending market, according to the incident report.",
        "url": "https://example.com/incident-report",
    }

    assert editorial.write_finding(item) is None
    assert "evidence_consistency_rejected=unsupported_numeric_claim" in capsys.readouterr().out


def test_rejects_same_number_with_different_asset_unit():
    ok, reason = check_draft_against_evidence(
        "The pool holds 100 USDC.",
        "The pool holds 100 ETH.",
    )
    assert not ok
    assert reason == "unsupported_numeric_claim"


def test_rejects_number_that_only_appears_as_substring_of_larger_value():
    ok, reason = check_draft_against_evidence(
        "The protocol processed 1000 transactions.",
        "The protocol processed 10000 transactions.",
    )
    assert not ok
    assert reason == "unsupported_numeric_claim"



def test_does_not_reject_standalone_year_missing_from_extracted_snippet():
    ok, reason = check_draft_against_evidence(
        "The proposal was published in 2026, but rollout is still pending.",
        "The proposal was published recently, but rollout is still pending.",
    )
    assert ok
    assert reason == "supported_literals"
