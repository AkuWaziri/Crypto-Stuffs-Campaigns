from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from collector import RawPost
from models import SourceAccount


TWITTERAPIS_SEARCH_URL = "https://api.twitterapis.com/twitter/tweet/advanced_search"

TWITTER_SOURCE = SourceAccount(
    "twitterapis_crypto",
    "Twitter/X Crypto",
    "x_crypto",
    90,
    90,
)


class TwitterAPIsError(RuntimeError):
    pass


class TwitterAPIsProvider:
    def __init__(self, api_key: str | None = None, timeout: int = 20):
        self.api_key = api_key or os.getenv("TWITTERAPIS_KEY")
        self.timeout = timeout
        if not self.api_key:
            raise TwitterAPIsError("TWITTERAPIS_KEY is not configured")

    def recent_posts(self, *, since: datetime, max_results: int = 20) -> list[RawPost]:
        # Broad crypto discovery: latest posts only, with retweets excluded.
        # Keep the query focused enough to avoid generic technology chatter.
        query = (
            "(crypto OR bitcoin OR ethereum OR solana OR stablecoin OR defi "
            "OR blockchain OR web3 OR airdrop OR memecoin OR tokenization) "
            "lang:en -is:retweet"
        )
        params = {
            "query": query,
            "product": "Latest",
        }
        url = f"{TWITTERAPIS_SEARCH_URL}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "User-Agent": "TrendsBot/0.3 (read-only crypto trend intelligence)",
            },
            method="GET",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise TwitterAPIsError(f"TwitterAPIs request failed: {exc}") from exc

        if payload.get("error"):
            raise TwitterAPIsError(f"TwitterAPIs returned error: {payload['error']}")

        posts: list[RawPost] = []
        for item in payload.get("tweets", [])[:max_results]:
            tweet_id = str(item.get("id", ""))
            text = item.get("text", "").strip()
            created_at = item.get("created_at")
            if not tweet_id or not text or not created_at:
                continue

            try:
                published_at = datetime.fromisoformat(
                    str(created_at).replace("Z", "+00:00")
                ).astimezone(timezone.utc)
            except ValueError:
                continue

            if published_at < since:
                continue

            metrics = item.get("public_metrics") or {}
            engagement = sum(
                int(metrics.get(key, 0) or 0)
                for key in (
                    "like_count",
                    "reply_count",
                    "retweet_count",
                    "quote_count",
                    "bookmark_count",
                )
            )
            username = ((item.get("author") or {}).get("userName") or "").strip()
            handle = username or "i"
            posts.append(
                RawPost(
                    signal_id=f"twitterapis-{tweet_id}",
                    text=text,
                    url=f"https://x.com/{handle}/status/{tweet_id}",
                    published_at=published_at,
                    engagement=engagement,
                )
            )

        return posts
