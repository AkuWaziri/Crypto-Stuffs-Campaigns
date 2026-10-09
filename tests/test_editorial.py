from editorial import build_editorial_digest, _score, _topic, _editorial_angles

def test_digest_includes_source_and_human_review():
    item = {
        "id": "a", "text": "New stablecoin payment API released with open source examples.",
        "url": "https://example.com/post", "source": "web", "views": 0,
    }
    digest = build_editorial_digest([item])
    assert "HUMAN REVIEW REQUIRED" in digest
    assert "https://example.com/post" in digest
    assert "verify the underlying claim" in digest
    assert "BUILD RADAR" in digest

def test_topic_classification_is_useful():
    assert _topic({"text": "A new stablecoin payment integration"}) == "Stablecoins & payments"
    assert _topic({"text": "Smart contract vulnerability and exploit analysis"}) == "Security"

def test_source_and_specificity_raise_priority():
    specific = {"text": "Open source SDK research finding and tutorial", "url": "https://example.com", "source": "github"}
    vague = {"text": "crypto update", "url": "", "source": "unknown"}
    assert _score(specific) > _score(vague)

def test_empty_input_returns_empty_digest():
    assert build_editorial_digest([]) == ""

def test_digest_respects_telegram_size():
    item = {"text": "Technical finding " + ("x" * 1000), "url": "https://example.com", "source": "web"}
    assert len(build_editorial_digest([item] * 5, limit=3)) <= 3900

def test_digest_provides_topic_specific_angles_and_post_scaffold():
    item = {"text": "A new stablecoin payment route changes transfer fees", "url": "https://example.com", "source": "web"}
    digest = build_editorial_digest([item])
    assert "DIFFERENTIATION ANGLES" in digest
    assert "Second order" in digest
    assert "Builder lens" in digest
    assert "POST SCAFFOLD" in digest
    assert "[verified change]" in digest

def test_angles_are_topic_specific():
    security = _editorial_angles({"text": "smart contract exploit"})
    payments = _editorial_angles({"text": "stablecoin payments"})
    assert "failure path" in security[0]
    assert "full path" in payments[0]
