import argparse
import os
from datetime import datetime, timedelta, timezone

os.environ.setdefault("VIRAL_SEEN_STATE_FILE", ".campaign_state.json")

from config import HIGH_PERFORMANCE_MAX_ITEMS, LOOKBACK_HOURS, MAX_FEED_ITEMS
from discovery import search_crypto_alpha, search_howto_research, search_skill_showcase
from editorial import clean_source_text, write_finding
from high_performance import _item_key, _url_key, _load_seen_ids, mark_sent, search_high_performing_x
from telegram import send_message
from web_sources import fetch_public_content


SOCIAL_SOURCES = {"x_high_performance", "x_social", "medium", "reddit", "telegram", "bluesky", "farcaster"}
WEB_SOURCES = {"web"}
SKILL_SOURCES = {"skill_research"}
HOWTO_SOURCES = {"howto_research"}


def _created_datetime(value):
    if value is None or value == "":
        return None
    try:
        if isinstance(value, (int, float)) or str(value).strip().isdigit():
            timestamp = float(value)
            if timestamp > 100000000000:
                timestamp /= 1000
            return datetime.fromtimestamp(timestamp, timezone.utc)
        created = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return created.replace(tzinfo=timezone.utc) if created.tzinfo is None else created.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _is_recent(item, cutoff):
    created = _created_datetime(item.get("created_at"))
    # Preserve candidates with missing/unparseable dates; the editorial layer must
    # not discard a useful finding solely because a platform has an odd timestamp.
    if created is None or created >= cutoff:
        return True
    # Practical how-to guides and setup docs stay useful beyond a breaking-news
    # cycle. Give this dedicated lane a 30-day discovery window while keeping
    # news/social findings constrained by the configured feed lookback.
    if item.get("source") == "howto_research":
        return created >= datetime.now(timezone.utc) - timedelta(days=30)
    return False


def _sort_key(item):
    created = _created_datetime(item.get("created_at"))
    return created.timestamp() if created else 0


def _unique_findings(groups, limit):
    """Deduplicate first, then deliberately balance social findings and web research."""
    seen = _load_seen_ids()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    candidates = []
    local_ids, local_keys, local_urls = set(), set(), set()

    for group in groups:
        for raw in group:
            item = dict(raw)
            item_id = str(item.get("id") or item.get("url") or "").strip()
            url = str(item.get("url") or "").strip()
            text = " ".join(str(item.get("text") or "").split())
            source = str(item.get("source") or "").lower()
            if source == "github" or not item_id or not url or not text:
                continue
            if not _is_recent(item, cutoff):
                continue

            item["id"] = item_id
            item["text"] = text
            key = _item_key(item)
            url_key = _url_key(item)
            if (
                item_id in seen or key in seen or (url_key and url_key in seen)
                or item_id in local_ids or key in local_keys
                or (url_key and url_key in local_urls)
            ):
                continue

            local_ids.add(item_id)
            local_keys.add(key)
            if url_key:
                local_urls.add(url_key)
            candidates.append(item)

    # Balance social findings, general web research, practical how-to guides,
    # and the separate professional skill-showcase lane.
    x_items = sorted(
        (x for x in candidates if x.get("source") == "x_high_performance"),
        key=lambda x: (int(x.get("views") or 0), _sort_key(x)),
        reverse=True,
    )
    other_social = sorted(
        (x for x in candidates if x.get("source") in SOCIAL_SOURCES and x.get("source") != "x_high_performance"),
        key=_sort_key,
        reverse=True,
    )
    web_items = sorted(
        (x for x in candidates if x.get("source") in WEB_SOURCES),
        key=_sort_key,
        reverse=True,
    )
    skill_items = sorted(
        (x for x in candidates if x.get("source") in SKILL_SOURCES),
        key=_sort_key,
        reverse=True,
    )
    howto_items = sorted(
        (x for x in candidates if x.get("source") in HOWTO_SOURCES),
        key=_sort_key,
        reverse=True,
    )
    other_items = sorted(
        (x for x in candidates if x.get("source") not in SOCIAL_SOURCES | WEB_SOURCES | SKILL_SOURCES | HOWTO_SOURCES),
        key=_sort_key,
        reverse=True,
    )

    selected, selected_ids = [], set()

    def take(items, count):
        for item in items:
            if len(selected) >= limit or count <= 0:
                break
            if item["id"] in selected_ids:
                continue
            selected.append(item)
            selected_ids.add(item["id"])
            count -= 1

    # At the current 13-item cap, target up to 5 high-performing X findings,
    # 2 other social posts, 2 general web findings, 2 how-to guides and 2
    # skill-led research leads. Both dedicated research lanes are independently capped.
    take(x_items, min(5, limit))
    take(other_social, min(2, max(0, limit - len(selected))))
    take(web_items, min(2, max(0, limit - len(selected))))
    take(howto_items, min(2, max(0, limit - len(selected))))
    take(skill_items, min(2, max(0, limit - len(selected))))
    take(other_items, limit - len(selected))
    # Fill remaining slots from general lanes only. Dedicated how-to and
    # skill-research quotas must not be bypassed by fallback selection.
    remaining_general = sorted(
        (x for x in candidates if x.get("source") not in SKILL_SOURCES | HOWTO_SOURCES),
        key=_sort_key,
        reverse=True,
    )
    take(remaining_general, limit - len(selected))
    return selected


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
    print("sources=x,web_news,howto_guides,docs_whitepapers_research_blogs,medium,reddit,telegram,bluesky,farcaster")
    print("github_feed=disabled")
    print("style=groq_analyst_findings_and_skill_showcase_posts_human_dna_source_linked")
    print(f"lookback_hours={LOOKBACK_HOURS}")
    print(f"max_per_run={MAX_FEED_ITEMS}")

    groups = []
    for label, fetcher in (
        ("x", search_high_performing_x),
        ("web_research", search_crypto_alpha),
        ("howto_research", search_howto_research),
        ("skill_showcase_research", search_skill_showcase),
        ("public_social", fetch_public_content),
    ):
        try:
            found = fetcher()
            print(f"source_lane={label} candidates={len(found)}")
            groups.append(found)
        except Exception as exc:
            print(f"source_lane_error={label}: {exc}")
            groups.append([])

    selected = _unique_findings(groups, MAX_FEED_ITEMS)
    print(f"findings_selected={len(selected)}")
    if not selected:
        print("findings_sent=0")
        return

    source_counts = {}
    delivered_items = []
    for item in selected:
        source = item.get("source", "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
        try:
            message = _format_finding(item)
        except Exception as exc:
            # Never degrade into raw reposts: skip when Groq cannot produce analysis.
            print(f"ai_writing_error={item['id']}: {exc}")
            continue
        if message is None:
            print(f"editorial_gate_skip={item['id']}: no substantive finding in available source material")
            continue
        try:
            delivered = send_message(message, dry_run=not args.telegram or args.test)
        except Exception as exc:
            print(f"delivery_error={item['id']}: {exc}")
            continue
        if delivered:
            delivered_items.append(item)

    if delivered_items:
        mark_sent(delivered_items)
    print(f"selected_source_counts={source_counts}")
    print(f"findings_sent={len(delivered_items)}")


if __name__ == "__main__":
    main()
