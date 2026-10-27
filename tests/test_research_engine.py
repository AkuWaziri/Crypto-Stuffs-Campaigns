from types import SimpleNamespace

import editorial
import main


def test_groq_unavailable_does_not_publish_generic_headline_fallback(capsys):
    item = {
        "id": "xrp-news-1",
        "text": "XRP News: Could Wallet Growth and Token Burns Shape Crypto?",
        "url": "https://news.google.com/rss/articles/example",
        "source": "web",
    }

    assert main._quota_fallback_finding(item) is None
    assert "fallback_publish_blocked=xrp-news-1" in capsys.readouterr().out


def test_google_news_wrapper_resolves_to_external_publisher(monkeypatch):
    monkeypatch.setattr(
        editorial.requests,
        "get",
        lambda *args, **kwargs: SimpleNamespace(
            url="https://publisher.example/crypto/xrp-wallet-growth",
            text="",
        ),
    )

    result = editorial._resolve_source_url(
        "https://news.google.com/rss/articles/example?oc=5"
    )

    assert result == "https://publisher.example/crypto/xrp-wallet-growth"


def test_google_news_wrapper_kept_when_it_cannot_be_resolved(monkeypatch):
    original = "https://news.google.com/rss/articles/example?oc=5"
    monkeypatch.setattr(
        editorial.requests,
        "get",
        lambda *args, **kwargs: SimpleNamespace(url=original, text="<html></html>"),
    )

    assert editorial._resolve_source_url(original) == original


def test_normal_publisher_url_does_not_trigger_resolution_request(monkeypatch):
    def fail_request(*args, **kwargs):
        raise AssertionError("ordinary publisher URLs should not be fetched for resolution")

    monkeypatch.setattr(editorial.requests, "get", fail_request)
    url = "https://publisher.example/article?utm_source=feed"

    assert editorial._resolve_source_url(url) == url


def test_research_triage_classifies_guides_and_scores_specific_evidence_higher():
    from research_engine import score_candidate

    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    generic = {
        "source": "web",
        "text": "XRP News: Could Wallet Growth and Token Burns Shape Crypto?",
        "url": "https://news.google.com/rss/articles/generic",
        "created_at": now.isoformat(),
    }
    specific = {
        "source": "web",
        "text": "Protocol postmortem identifies 0x1234567890abcdef as the exploited contract; 2.4 million USDC moved in the incident.",
        "url": "https://docs.protocol.example/security/postmortem",
        "created_at": now.isoformat(),
    }
    guide = {
        "source": "howto_research",
        "content_lane": "research_guides",
        "text": "How to inspect a wallet transaction using a block explorer.",
        "url": "https://docs.example/guide",
        "created_at": now.isoformat(),
    }

    generic_score = score_candidate(generic, now=now)
    specific_score = score_candidate(specific, now=now)
    guide_score = score_candidate(guide, now=now)

    assert specific_score["score"] > generic_score["score"]
    assert specific_score["content_type"] == "investigation"
    assert guide_score["content_type"] == "education"


def test_research_record_upserts_status_and_bounds_snippet(monkeypatch, tmp_path):
    import research_records

    state_file = tmp_path / "research_records.json"
    monkeypatch.setattr(research_records, "RESEARCH_RECORDS_FILE", state_file)
    item = {
        "id": "record-1",
        "source": "web",
        "text": "Protocol proposes a new stablecoin market with a published collateral factor.",
        "url": "https://docs.protocol.example/proposal",
        "created_at": "2026-10-27T10:00:00+00:00",
    }

    research_records.record_candidate(item, "selected_for_research")
    research_records.record_candidate(item, "published", draft="A researched finding.\n\nSource: https://docs.protocol.example/proposal")

    records = research_records.load_research_records()
    assert len(records) == 1
    assert records[0]["status"] == "published"
    assert records[0]["content_type"] == "breaking_news"
    assert records[0]["priority_score"] is not None
    assert records[0]["draft"].startswith("A researched finding")
