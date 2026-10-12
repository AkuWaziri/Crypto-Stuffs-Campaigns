from datetime import datetime, timezone

import main


def item(source, number, *, text=None, url=None, views=0):
    return {
        "id": f"{source}:{number}",
        "source": source,
        "author": "test",
        "text": text or f"Distinct {source} crypto finding number {number} with useful details.",
        "url": url or f"https://example.com/{source}/{number}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "views": views,
    }


def test_selection_reserves_skill_research_slots_and_excludes_github(monkeypatch):
    monkeypatch.setattr(main, "_load_seen_ids", lambda: set())
    social = [item("farcaster", n) for n in range(25)]
    web = [item("web", n) for n in range(10)]
    skill = [item("skill_research", n) for n in range(5)]
    for entry in skill:
        entry["content_lane"] = "skill_showcase"
        entry["skill_profile"] = "points_campaign_designer"
    github = [item("github", n) for n in range(5)]

    selected = main._unique_findings([[], web + github, skill, social], 13)

    assert len(selected) == 13
    assert all(x["source"] != "github" for x in selected)
    assert sum(x["source"] == "skill_research" for x in selected) == 2
    assert sum(x["source"] == "web" for x in selected) >= 1


def test_selection_prefers_x_and_deduplicates_tracking_url_variants(monkeypatch):
    monkeypatch.setattr(main, "_load_seen_ids", lambda: set())
    now = datetime.now(timezone.utc).isoformat()
    x_post = item("x_high_performance", 1, text="A unique post about stablecoin payment rails", views=90000)
    medium_a = item(
        "medium", 2, text="Same story about a new crypto protocol",
        url="https://medium.com/story?source=rss&utm_campaign=crypto",
    )
    medium_b = item(
        "medium", 3, text="Different wording that should not hide a URL duplicate",
        url="https://medium.com/story?source=tag&ref=homepage",
    )
    medium_a["created_at"] = now
    medium_b["created_at"] = now

    selected = main._unique_findings([[x_post], [], [medium_a, medium_b]], 10)

    assert x_post in selected
    assert len([x for x in selected if x["url"].startswith("https://medium.com/story")]) == 1


def test_old_and_duplicate_items_are_filtered(monkeypatch):
    old = item("farcaster", 1)
    old["created_at"] = "2020-01-01T00:00:00+00:00"
    duplicate = item("web", 2, text="Repeated title and content across RSS feeds")
    same_text = item("medium", 3, text="Repeated title and content across RSS feeds")
    monkeypatch.setattr(main, "_load_seen_ids", lambda: set())

    selected = main._unique_findings([[old, duplicate], [same_text]], 30)

    assert old not in selected
    assert len([x for x in selected if "Repeated title" in x["text"]]) == 1



def test_selection_reserves_howto_and_skill_research_without_exceeding_cap(monkeypatch):
    monkeypatch.setattr(main, "_load_seen_ids", lambda: set())
    x = [item("x_high_performance", n, views=50000 + n) for n in range(15)]
    web = [item("web", n) for n in range(8)]
    howto = [item("howto_research", n) for n in range(6)]
    skill = [item("skill_research", n) for n in range(6)]
    for entry in howto:
        entry["content_lane"] = "research_guides"
    for entry in skill:
        entry["content_lane"] = "skill_showcase"

    selected = main._unique_findings([x, web, howto, skill], 13)

    assert len(selected) == 13
    assert sum(entry["source"] == "howto_research" for entry in selected) == 3
    assert sum(entry["source"] == "skill_research" for entry in selected) == 2
    assert all(entry["source"] != "github" for entry in selected)
