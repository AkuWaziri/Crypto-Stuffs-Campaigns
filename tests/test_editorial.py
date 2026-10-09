from types import SimpleNamespace

import editorial


class FakeCompletions:
    def create(self, **kwargs):
        assert kwargs["model"]
        assert "human writing DNA" in kwargs["messages"][0]["content"]
        source_payload = kwargs["messages"][1]["content"]
        assert "<div" not in source_payload
        assert "&#xFC;" not in source_payload
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="A concrete finding with the supplied numbers, and no invented claims."
                    )
                )
            ]
        )


class FakeClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=FakeCompletions())


def test_write_finding_keeps_exact_source_link_and_cleans_html(monkeypatch):
    monkeypatch.setattr(editorial, "_client", lambda: FakeClient())
    item = {
        "id": "test-1",
        "source": "medium",
        "author": "researcher",
        "text": "Mining tools <div class='medium-feed-item'><p>Ein kleines Set f&#xFC;r Bitcoin.</p><img src='image.png'></div>",
        "url": "https://example.com/original-post",
        "created_at": "2026-10-09T10:00:00+00:00",
        "views": 25000,
    }

    result = editorial.write_finding(item)

    assert result.startswith("A concrete finding")
    assert "<div" not in result
    assert "medium-feed-item" not in result
    assert result.endswith("Source: https://example.com/original-post")
    assert result.count(item["url"]) == 1


def test_clean_source_text_decodes_entities_and_strips_markup():
    result = editorial.clean_source_text(
        "<p>Ein kleines Set f&#xFC;r Bitcoin</p><img src='hidden.png'>"
    )
    assert result == "Ein kleines Set für Bitcoin"
    assert "<p>" not in result
    assert "hidden.png" not in result


def test_write_finding_requires_source_url():
    try:
        editorial.write_finding({"text": "No URL here"})
    except ValueError as exc:
        assert "source URL" in str(exc)
    else:
        raise AssertionError("Expected missing source URL to be rejected")
