from types import SimpleNamespace

import editorial


class FakeCompletions:
    def __init__(self):
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs
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



def test_skill_showcase_uses_profile_and_requires_publishable_research(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(editorial, "_client", lambda: fake)
    monkeypatch.setattr(editorial, "_fetch_article_text", lambda url: "Official documentation describes the protocol's points eligibility and referral rules in detail.")
    item = {
        "id": "skill-test",
        "source": "skill_research",
        "content_lane": "skill_showcase",
        "skill_profile": "points_campaign_designer",
        "niche": "skill showcase: points campaign design",
        "text": "Protocol docs describe points eligibility, referral attribution, and anti-Sybil controls.",
        "url": "https://example.com/points-docs",
        "created_at": "2026-10-10T10:00:00+00:00",
    }

    result = editorial.write_finding(item)

    request = fake.chat.completions.last_request
    prompt = request["messages"][1]["content"]
    assert "points_campaign_designer" in prompt
    assert "publish-ready post" in prompt
    assert "anti-Sybil" in prompt
    assert "legal advice" in prompt
    assert result.endswith("Source: https://example.com/points-docs")
