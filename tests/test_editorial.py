from types import SimpleNamespace

import editorial


class FakeCompletions:
    def create(self, **kwargs):
        assert kwargs["model"]
        assert "human writing DNA" in kwargs["messages"][0]["content"]
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


def test_write_finding_keeps_exact_source_link(monkeypatch):
    monkeypatch.setattr(editorial, "_client", lambda: FakeClient())
    item = {
        "id": "test-1",
        "source": "x",
        "author": "researcher",
        "text": "A finding with concrete details.",
        "url": "https://example.com/original-post",
        "created_at": "2026-10-09T10:00:00+00:00",
        "views": 25000,
    }

    result = editorial.write_finding(item)

    assert result.startswith("A concrete finding")
    assert result.endswith("Source: https://example.com/original-post")
    assert result.count(item["url"]) == 1


def test_write_finding_requires_source_url():
    try:
        editorial.write_finding({"text": "No URL here"})
    except ValueError as exc:
        assert "source URL" in str(exc)
    else:
        raise AssertionError("Expected missing source URL to be rejected")
