import argparse
from datetime import datetime, timedelta, timezone
from classifier import classify, is_relevant
from config import ENABLE_WEB_SOURCES, LOOKBACK_HOURS, MAX_FEED_ITEMS
from feed import format_item
from telegram import send_message
from web_sources import fetch_public_campaigns
from x_scraper import search_x

def recent(item):
    raw = item.get("created_at")
    if not raw: return True
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")) >= datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    except ValueError:
        return True

def main():
    parser = argparse.ArgumentParser(description="Crypto-Stuffs-Campaigns")
    parser.add_argument("--telegram", action="store_true")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    print("CRYPTO-STUFFS-CAMPAIGNS")
    print("mode=read-only")
    print("execution=disabled")
    print("sources=X + public crypto campaign platforms")
    items = []
    try: items.extend(search_x())
    except Exception as exc: print(f"x_error={exc}")
    if ENABLE_WEB_SOURCES: items.extend(fetch_public_campaigns())
    clean, seen = [], set()
    for item in items:
        item = classify(item)
        if not recent(item) or not is_relevant(item): continue
        key = item.get("url") or item.get("id")
        if key in seen: continue
        seen.add(key); clean.append(item)
    clean.sort(key=lambda x: x.get("campaign_score", 0), reverse=True)
    selected = clean[:MAX_FEED_ITEMS]
    for item in selected: send_message(format_item(item), dry_run=not args.telegram or args.test)
    print(f"discovered={len(items)}"); print(f"relevant={len(clean)}"); print(f"sent={len(selected)}")

if __name__ == "__main__":
    main()
