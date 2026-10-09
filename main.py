import argparse
import os
from datetime import datetime, timedelta, timezone

os.environ.setdefault("VIRAL_SEEN_STATE_FILE", ".campaign_state.json")

from config import HIGH_PERFORMANCE_MAX_ITEMS, LOOKBACK_HOURS
from discovery import search_crypto_alpha
from editorial import clean_source_text, write_finding
from high_performance import _item_key, _load_seen_ids, mark_sent, search_high_performing_x
from telegram import send_message
from web_sources import fetch_public_content


def _is_recent(item, cutoff):
    value = item.get("created_at")
    if not value:
        return True
    try:
        if isinstance(value, (int, float)):
            created = datetime.fromtimestamp(value, timezone.utc)
        else:
            created = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
        return created >= cutoff
    except (TypeError, ValueError, OverflowError, OSError):
        return True


def _unique_findings(groups, limit):
    seen = _load_seen_ids()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    selected, local_ids, local_keys = [], set(), set()
    for group in groups:
        for raw in group:
            item = dict(raw)
            item_id = str(item.get("id") or item.get("url") or "").strip()
            url = str(item.get("url") or "").strip()
            text = " ".join(str(item.get("text") or "").split())
            if not item_id or not url or not text or not _is_recent(item, cutoff):
                continue
            item["id"] = item_id
            item["text"] = text
            key = _item_key(item)
            if item_id in seen or key in seen or item_id in local_ids or key in local_keys:
                continue
            local_ids.add(item_id)
            local_keys.add(key)
            selected.append(item)
    selected.sort(key=lambda x: str(x.get("created_at") or ""), reverse=True)
    return selected[:limit]


def _format_finding(item):
    """Generate the human-DNA write-up and preserve the direct source link."""
    return write_finding(item)


def main():
    parser = argparse.ArgumentParser(description="Crypto-Stuffs-Campaigns")
    parser.add_argument("--telegram", action="store_true")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    print("CRYPTO-STUFFS")
    print("mode=read-only")
    print("feed=ai_written_crypto_findings")
    print("sources=x,news,github,reddit,medium,telegram,bluesky,farcaster")
    print("style=openai_human_dna_source_linked")
    print(f"lookback_hours={LOOKBACK_HOURS}")
    print(f"max_per_run={HIGH_PERFORMANCE_MAX_ITEMS}")

    groups = []
    for label, fetcher in (
        ("x", search_high_performing_x),
        ("news_and_builds", search_crypto_alpha),
        ("public_social", fetch_public_content),
    ):
        try:
            found = fetcher()
            print(f"source_lane={label} candidates={len(found)}")
            groups.append(found)
        except Exception as exc:
            print(f"source_lane_error={label}: {exc}")
            groups.append([])

    selected = _unique_findings(groups, HIGH_PERFORMANCE_MAX_ITEMS)
    if not selected:
        print("findings_selected=0")
        print("findings_sent=0")
        return

    delivered_items = []
    for item in selected:
        try:
            message = _format_finding(item)
        except Exception as exc:
            # Keep the source material usable if the AI API is temporarily unavailable.
            print(f"ai_writing_error={item['id']}: {exc}")
            message = f"{clean_source_text(item['text'])}\n\nSource: {item['url']}"
        try:
            delivered = send_message(message, dry_run=not args.telegram or args.test)
        except Exception as exc:
            print(f"delivery_error={item['id']}: {exc}")
            continue
        if delivered:
            delivered_items.append(item)

    if delivered_items:
        mark_sent(delivered_items)
    print(f"findings_selected={len(selected)}")
    print(f"findings_sent={len(delivered_items)}")


if __name__ == "__main__":
    main()
