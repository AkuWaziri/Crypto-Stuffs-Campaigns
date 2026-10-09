from types import SimpleNamespace

import web_sources


def test_item_removes_html_and_decodes_entities():
    item = web_sources._item(
        "medium",
        "author",
        "Headline <div class='medium-feed-item'><p>Ein kleines Set f&#xFC;r Bitcoin.</p>"
        "<img src='https://example.com/image.png'></div>",
        "https://example.com/post",
    )

    assert item["text"] == "Headline Ein kleines Set für Bitcoin."
    assert "<div" not in item["text"]
    assert "image.png" not in item["text"]


def test_rss_parses_medium_description_as_plain_text(monkeypatch):
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <rss><channel><item>
      <title>Bitcoin mining tools</title>
      <description>&lt;div class="medium-feed-item"&gt;&lt;p&gt;Ein kleines Set f&amp;#xFC;r Menschen.&lt;/p&gt;&lt;img src="image.png"/&gt;&lt;/div&gt;</description>
      <link>https://example.com/post</link>
      <pubDate>Fri, 09 Oct 2026 10:00:00 GMT</pubDate>
    </item></channel></rss>"""

    monkeypatch.setattr(
        web_sources.requests,
        "get",
        lambda *args, **kwargs: SimpleNamespace(
            content=xml,
            raise_for_status=lambda: None,
        ),
    )

    items = web_sources._rss("https://example.com/feed.xml", "medium")

    assert len(items) == 1
    assert items[0]["text"].startswith("Bitcoin mining tools.")
    assert "<div" not in items[0]["text"]
    assert "image.png" not in items[0]["text"]
    assert "Ein kleines Set" in items[0]["text"]
