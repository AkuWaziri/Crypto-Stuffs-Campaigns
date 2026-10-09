from editorial import _extract_json, _fallback, _prompt, write_findings


def test_prompt_preserves_source_id_and_evidence():
    item = {
        "id": "reddit:https://reddit.com/r/test/1",
        "source": "reddit",
        "author": "tester",
        "created_at": "2026-10-09T10:00:00+00:00",
        "title": "Wallets move tokens",
        "text": "59 wallets moved tokens after five months.",
        "url": "https://reddit.com/r/test/1",
    }
    prompt = _prompt([item])
    assert "59 wallets moved tokens after five months." in prompt
    assert item["id"] in prompt
    assert "Do not invent facts" in prompt


def test_extract_json_with_fences():
    parsed = _extract_json('```json\n{"items":[{"id":"x","story":"A finding."}]}\n```')
    assert parsed["items"][0]["story"] == "A finding."


def test_fallback_uses_original_source_text():
    assert _fallback({"id": "x", "text": "A real crypto finding."}) == "A real crypto finding."


def test_write_findings_falls_back_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    items = [{"id": "x", "text": "source text", "url": "https://example.com"}]
    assert write_findings(items) == {"x": "source text"}
