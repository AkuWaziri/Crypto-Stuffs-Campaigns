from __future__ import annotations

import os
from datetime import datetime, timezone

from collector import collect_fresh_signals
from config import MAX_SIGNAL_AGE_MINUTES, MODE
from narrative_engine import build_narratives
from rss_provider import CryptoRSSProvider
from sources import enabled_sources
from trend_feed import format_feed, send_telegram


def main() -> None:
    now = datetime.now(timezone.utc)
    signals = collect_fresh_signals(
        CryptoRSSProvider(),
        enabled_sources(),
        now=now,
        max_age_minutes=MAX_SIGNAL_AGE_MINUTES,
    )
    narratives = build_narratives(
        signals,
        now=now,
        max_age_minutes=MAX_SIGNAL_AGE_MINUTES,
    )

    print("=== TRENDSBOT CRYPTO TREND FEED ===")
    print(f"mode={MODE}; execution=disabled; max_signal_age_minutes={MAX_SIGNAL_AGE_MINUTES}")
    print(f"signals={len(signals)} trends={len(narratives)}")

    text = format_feed(narratives)
    send_telegram(text, os.getenv("TELEGRAM_BOT_TOKEN", ""), os.getenv("TELEGRAM_CHAT_ID", ""))
    print("telegram=sent")


if __name__ == "__main__":
    main()
