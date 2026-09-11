from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from collector import RawPost
from models import SourceAccount


X_RECENT_SEARCH_URL = "https://api.x.com/2/tweets/search/recent"


class XApiError(RuntimeError):
    pass


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class XRecentSearchProvider:
    def __init__(self, bearer_token: str | None = None):
        self.bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN")
        if not self.bearer_token:
            raise XApiError("X_BEARER_TOKEN is not configured")

    def recent_posts(self, source: SourceAccount, *, since: datetime) -> list[RawPost]:
        # Account-scoped recent search avoids depending on a fixed user ID list.
        query = f"from:{source.handle} -is:retweet"
        params = {
            "query": query,
            "max_results": "10",
            "start_time": _iso_z(since - timedelta(seconds=30)),
            "tweet.fields": "created_at,public_metrics,author_id",
        }
        url = f"{X_RECENT_SEARCH_URL}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "Accept": "application/json",
                "User-Agent": "TrendsBot/0.1 (read-only trend intelligence)",
            },
            method="GET",
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise XApiError(f"X recent-search request failed: {exc}") from exc

        if payload.get("errors"):
            raise XApiError(f"X API returned errors: {payload['errors']}")

        posts: list[RawPost] = []
        for item in payload.get("data", []):
            created_at = item.get("created_at")
            if not created_at:
                continue
            metrics = item.get("public_metrics") or {}
            engagement = sum(
                int(metrics.get(key, 0) or 0)
                for key in ("like_count", "reply_count", "repost_count", "quote_count")
            )
            posts.append(
                RawPost(
                    signal_id=item["id"],
                    text=item.get("text", ""),
                    url=f"https://x.com/{source.handle}/status/{item['id']}",
                    published_at=datetime.fromisoformat(created_at.replace("Z", "+00:00")),
                    engagement=engagement,
                )
            )
        return posts
