from datetime import datetime, timedelta, timezone

from twitterapis_provider import TWITTER_SOURCE, TwitterAPIsProvider


def test_parses_twitterapis_response(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'''{
                "tweets": [{
                    "id": "123",
                    "text": "Solana stablecoin payments are growing",
                    "created_at": "Sun Sep 13 14:00:00 +0000 2026",
                    "author": {"username": "crypto_user"},
                    "favorite_count": 10,
                    "retweet_count": 5,
                    "reply_count": 2,
                    "quote_count": 1,
                    "bookmark_count": 3
                }]
            }'''

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: FakeResponse())
    provider = TwitterAPIsProvider(api_key="test")
    posts = provider.recent_posts(
        since=datetime(2026, 9, 13, 13, 0, tzinfo=timezone.utc)
    )

    assert len(posts) == 1
    assert posts[0].signal_id == "twitterapis-123"
    assert posts[0].url == "https://x.com/crypto_user/status/123"
    assert posts[0].engagement == 21
    assert posts[0].published_at == datetime(2026, 9, 13, 14, 0, tzinfo=timezone.utc)


def test_ignores_posts_older_than_window(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'''{"tweets": [{"id": "old", "text": "old", "created_at": "Sun Sep 13 10:00:00 +0000 2026", "author": {"username": "u"}}]}'''

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: FakeResponse())
    provider = TwitterAPIsProvider(api_key="test")
    posts = provider.recent_posts(
        since=datetime(2026, 9, 13, 13, 0, tzinfo=timezone.utc)
    )

    assert posts == []
