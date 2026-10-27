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
