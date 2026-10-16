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



def test_howto_research_prompt_requires_reproducible_steps_and_source(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(editorial, "_client", lambda: fake)
    monkeypatch.setattr(editorial, "_fetch_article_text", lambda url: "Official documentation provides prerequisites, the free tier limits, and exact setup steps for an API account.")
    item = {
        "id": "howto-test",
        "source": "howto_research",
        "content_lane": "research_guides",
        "niche": "free-first AI API setup guide",
        "text": "How to configure a free API tier with documented usage limits and verification steps.",
        "url": "https://example.com/free-api-guide",
        "created_at": "2026-10-10T10:00:00+00:00",
    }

    result = editorial.write_finding(item)

    prompt = fake.chat.completions.last_request["messages"][1]["content"]
    assert "step-by-step how-to guide" in prompt
    assert "free tier" in prompt
    assert "profit promise" in prompt
    assert result.endswith("Source: https://example.com/free-api-guide")



def test_bing_news_redirect_is_unwrapped_to_publisher_url():
    redirect = (
        "http://www.bing.com/news/apiclick.aspx?ref=feed&url="
        "https%3a%2f%2fexample.com%2fnews%2fthai-etf%3futm_source%3dfeed"
    )
    assert editorial._direct_source_url(redirect) == "https://example.com/news/thai-etf?utm_source=feed"


def test_incomplete_editorial_output_is_rejected():
    result = editorial._validate_generated_finding(
        "October 16 marks the day the legal permission",
        "https://example.com/regulatory-rules",
    )
    assert result is None


def test_editorial_output_removes_model_sources_section_and_appends_one_source():
    result = editorial._validate_generated_finding(
        "The rule took effect on October 16, 2024. That did not confirm a specific ETF listing.\n\n"
        "SOURCES\n- Bing tracking link\n- another source",
        "https://example.com/regulatory-rules",
    )
    assert result == (
        "The rule took effect on October 16, 2024. That did not confirm a specific ETF listing."
        "\n\nSource: https://example.com/regulatory-rules"
    )
    assert result.count("Source:") == 1
    assert "SOURCES" not in result
