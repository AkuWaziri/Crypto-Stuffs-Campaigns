from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from crypto_relevance import is_crypto_relevant
from narrative_engine import build_narratives
from trend_feed import format_feed, send_telegram
from twitterapis_provider import TwitterAPIsProvider


MAX_AGE_MINUTES = 24 * 60


def main() -> None:
    now = datetime.now(timezone.utc)
    provider = TwitterAPIsProvider()
    posts = provider.recent_posts(since=now - timedelta(minutes=MAX_AGE_MINUTES))

    narratives = build_narratives(
        [
            # Convert RawPost objects into the normal FreshSignal model used by
            # the existing narrative/feed pipeline.
            provider_signal
            for provider_signal in []
        ],
        now=now,
        max_age_minutes=MAX_AGE_MINUTES,
    )

    # TwitterAPIs already returns RawPost objects. Keep the conversion local so
    # the existing RSS/source pipeline remains untouched.
    from models import FreshSignal
    from twitterapis_provider import TWITTER_SOURCE

    signals = [
        FreshSignal(
            source=TWITTER_SOURCE,
            signal_id=post.signal_id,
            text=post.text,
            url=post.url,
            published_at=post.published_at,
            engagement=post.engagement,
        )
        for post in posts
    ]
    narratives = build_narratives(signals, now=now, max_age_minutes=MAX_AGE_MINUTES)
    crypto_narratives = [
        narrative
        for narrative in narratives
        if is_crypto_relevant(
            narrative.title,
            " ".join(signal.text for signal in narrative.signals),
        )
    ]

    print("=== TRENDSBOT TWITTER/X DAILY FEED ===")
    print("mode=twitter-daily; execution=disabled; source=TwitterAPIs")
    print(
        f"tweets={len(posts)} trends={len(narratives)} "
        f"crypto_trends={len(crypto_narratives)}"
    )

    text = format_feed(crypto_narratives)
    send_telegram(
        text,
        os.getenv("TELEGRAM_BOT_TOKEN", ""),
        os.getenv("TELEGRAM_CHAT_ID", ""),
    )
    print("telegram=sent")


if __name__ == "__main__":
    main()
