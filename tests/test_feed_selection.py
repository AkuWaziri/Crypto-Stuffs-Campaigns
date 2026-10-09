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


def test_selection_balances_social_and_web_and_excludes_github(monkeypatch):
    monkeypatch.setattr(main, "_load_seen_ids", lambda: set())
    social = [item("farcaster", n) for n in range(25)]
    web = [item("web", n) for n in range(10)]
    github = [item("github", n) for n in range(5)]

    selected = main._unique_findings([[], web + github, social], 30)

    assert len(selected) == 30
    assert all(x["source"] != "github" for x in selected)
    assert sum(x["source"] in main.SOCIAL_SOURCES for x in selected) == 20
    assert sum(x["source"] == "web" for x in selected) == 10


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
