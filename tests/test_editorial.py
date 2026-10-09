from editorial import build_editorial_digest, build_post_recommendation, _score, _topic, _editorial_angles

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

def test_each_feed_item_gets_a_specific_content_recommendation():
    security = build_post_recommendation({"text": "Smart contract exploit exposes a permission bug", "url": "https://example.com/security"})
    payments = build_post_recommendation({"text": "New stablecoin payment route cuts fees", "url": "https://example.com/payments"})
    assert "CONTENT RECOMMENDATION" in security
    assert "failure path" in security.lower()
    assert "total fees" in payments.lower()
    assert "Hook to develop" in payments
    assert build_post_recommendation({"text": "missing source"}) == ""

def test_content_recommendation_is_compact():
    item = {"text": "New stablecoin payment route released " + ("details " * 100), "url": "https://example.com", "source": "web"}
    assert len(build_post_recommendation(item)) < 1000

def test_recommendation_uses_specific_post_details_and_research_questions():
    item = {"text": "Stablecoin volume rose 42% after the new payment route launched", "url": "https://example.com/data", "source": "web"}
    rec = build_post_recommendation(item)
    assert "42%" in rec
    assert "baseline" in rec.lower()
    assert "Evidence to collect" in rec
    assert "Your analysis question" in rec

def test_x_recommendation_does_not_claim_verification_without_flag():
    item = {"text": "Crypto protocol update", "url": "https://x.com/example/status/1", "source": "x_high_performance", "author": "example"}
    rec = build_post_recommendation(item)
    assert "verified X account" not in rec
