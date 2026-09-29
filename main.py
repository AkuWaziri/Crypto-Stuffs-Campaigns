import argparse
from datetime import datetime, timedelta, timezone

from classifier import classify, is_relevant
from config import ENABLE_WEB_SOURCES, LOOKBACK_HOURS
from feed import format_item
from state import load_seen, save_seen
from telegram import send_message
from web_sources import fetch_public_content
from x_scraper import search_x

def recent(item):
    raw = item.get("created_at")
    if not raw:
        return True
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt >= datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    except (ValueError, TypeError):
        return True

def main():
    parser = argparse.ArgumentParser(description="Crypto-Stuffs-Campaigns")
    parser.add_argument("--telegram", action="store_true")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    print("CRYPTO-STUFFS")
    print("mode=read-only")
    print("execution=disabled")
    print("sources=X + Reddit + Medium + Telegram + Bluesky")

    items = []
    try:
        items.extend(search_x())
    except Exception as exc:
        print(f"x_error={exc}")
    if ENABLE_WEB_SOURCES:
        items.extend(fetch_public_content())

    seen = load_seen()
    new_seen = set(seen)
    clean = []
    for item in items:
        item = classify(item)
        if not recent(item) or not is_relevant(item):
            continue
        key = item.get("url") or item.get("id")
        if not key or key in seen:
            continue
        new_seen.add(key)
        clean.append(item)

    # No signal/quality scoring, ranking, or item-count cap.
    # Every new item that passes the relevance filters is sent in this scheduled run.
    selected = clean

    for item in selected:
        send_message(format_item(item), dry_run=not args.telegram or args.test)

    save_seen(new_seen)
    print(f"discovered={len(items)}")
    print(f"new_relevant={len(clean)}")
    print(f"sent={len(selected)}")

if __name__ == "__main__":
    main()
