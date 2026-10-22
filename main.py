import argparse
import os
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
import re

os.environ.setdefault("VIRAL_SEEN_STATE_FILE", ".campaign_state.json")

from config import HIGH_PERFORMANCE_MAX_ITEMS, LOOKBACK_HOURS, MAX_FEED_ITEMS
from discovery import search_crypto_alpha, search_howto_research, search_skill_showcase
import editorial as editorial_module
from editorial import GroqQuotaExhaustedError, clean_source_text, write_finding
from high_performance import _item_key, _url_key, _load_seen_ids, _load_seen_texts, mark_sent, search_high_performing_x
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


def _normalized_content(value):
    text = str(value or "").lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _near_duplicate(text, history):
    """Catch repeated headlines/posts with different URLs or RSS snippets."""
    normalized = _normalized_content(text)
    # Keep this fuzzy gate for substantial snippets; short titles are too
    # noisy and can share generic crypto vocabulary without being duplicates.
    if len(normalized) < 90:
        return False
    tokens = {word for word in normalized.split() if len(word) > 2}
    if len(tokens) < 10:
        return False
    for old in history:
        if not old or len(old) < 55:
            continue
        if normalized == old:
            return True
        old_tokens = {word for word in old.split() if len(word) > 2}
        if len(old_tokens) < 8:
            continue
        overlap = len(tokens & old_tokens) / max(1, len(tokens | old_tokens))
        if overlap >= 0.78 or SequenceMatcher(None, normalized[:240], old[:240]).ratio() >= 0.88:
            return True
    return False


def _unique_findings(groups, limit):
    """Deduplicate exact and near-identical findings before source balancing."""
    seen = _load_seen_ids()
    history = _load_seen_texts()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    candidates = []
    local_ids, local_keys, local_urls = set(), set(), set()
    local_texts = set()

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
            normalized_text = _normalized_content(text)
            if (
                item_id in seen or key in seen or (url_key and url_key in seen)
                or item_id in local_ids or key in local_keys
                or (url_key and url_key in local_urls)
                or _near_duplicate(text, history)
                or _near_duplicate(text, local_texts)
            ):
                continue

            local_ids.add(item_id)
            local_keys.add(key)
            local_texts.add(normalized_text)
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

    # Scale source quotas with the larger backfill buffer so rejected weak items
    # can be replaced by later candidates from the same lanes.
    quota_scale = max(1, (limit + 12) // 13)
    take(x_items, min(4 * quota_scale, limit))
    take(other_social, min(2 * quota_scale, max(0, limit - len(selected))))
    take(web_items, min(2 * quota_scale, max(0, limit - len(selected))))
    take(howto_items, min(3 * quota_scale, max(0, limit - len(selected))))
    take(skill_items, min(2 * quota_scale, max(0, limit - len(selected))))
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


def _quota_fallback_finding(item):
    """Create a complete, concise tweet draft without copying truncated RSS prose."""
    text = clean_source_text(item.get("text") or "")
    url = str(item.get("url") or "").strip()
    if not text or not url:
        return None

    # RSS feeds often repeat titles, append publisher names, or end mid-sentence.
    headline = re.split(r"\s+-\s+", text, maxsplit=1)[0].strip()
    if "…" in headline or "..." in headline:
        boundary = max(headline.rfind(". "), headline.rfind("! "), headline.rfind("? "))
        if boundary > 30:
            headline = headline[:boundary + 1]
        else:
            headline = re.split(r"(?:…|\.{3})", headline, maxsplit=1)[0].strip()
    headline = re.sub(r"^(?:SCOOP|BREAKING|JUST IN|EXCLUSIVE)\s*:\s*", "", headline, flags=re.I)
    headline = re.sub(r",?\s*sources? told [A-Z][A-Za-z0-9 .&-]+[.!]?$", "", headline, flags=re.I).strip(" .,:;-")

    words = headline.split()
    for size in range(len(words) // 2, 5, -1):
        removed = False
        for start_idx in range(0, len(words) - (2 * size) + 1):
            if words[start_idx:start_idx + size] == words[start_idx + size:start_idx + (2 * size)]:
                words = words[:start_idx + size] + words[start_idx + (2 * size):]
                removed = True
                break
        if removed:
            break
    headline = " ".join(words).strip(" -|")
    lower = headline.lower()

    vague = (
        "gm everyone", "good morning", "huge news", "this is bullish",
        "game changer", "mass adoption is coming", "don't miss out",
    )
    concrete = (
        "0x", "transaction", "exploit", "hack", "vulnerab", "security flaw",
        "security flaws", "warn", "warning", "launch", "launched", "release",
        "released", "upgrade", "proposal", "mainnet", "testnet", "wallet",
        "protocol", "api", "sdk", "fees", "revenue", "volume", "users",
        "million", "billion", "%", "stablecoin", "payment", "deploy",
        "open source", "documentation", "how to", "guide", "tutorial",
        "points", "governance", "bridge", "liquidity", "agent", "bank",
        "account",
    )
    if any(term in lower for term in vague) and not any(term in lower for term in concrete):
        return None
    if len(headline) < 35 or not any(term in lower for term in concrete):
        return None

    if "agent" in lower and any(term in lower for term in ("bank", "customer account", "user instruction")):
        claim = headline[0].lower() + headline[1:] if headline else headline
        draft = (
            f"Reports say {claim.rstrip('.')} . "
            "The key security question is how banks distinguish user-approved automation "
            "from actions customers never authorized."
        ).replace(" .", ".")
    elif any(term in lower for term in ("security flaw", "security flaws", "vulnerab", "exploit", "hack")):
        draft = f"Security note: {headline}. Check the original advisory for affected versions and available fixes before assuming a service is safe."
    else:
        draft = f"{headline.rstrip('.')} is worth tracking. Verify the source details and who is affected before acting."
    if len(draft) > 275:
        draft = draft[:272].rsplit(" ", 1)[0].rstrip(" ,;:-") + "…"
    draft = draft.rstrip(" .,:;-…")
    if not draft or draft.lower().split()[-1] in {"and", "or", "but", "with", "to", "for", "the", "a", "an", "of"}:
        return None
    return f"Tweet draft (Groq temporarily unavailable):\n\n{draft}\n\nSource: {url}"

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

    # Use a 6x candidate buffer, but stop writing immediately when the delivery
    # target is reached. This lets the editorial gate replace weak candidates
    # without lowering quality or fabricating posts to fill the feed.
    # Keep a small backfill pool so editorial screening cannot fan out into dozens
    # of token-consuming model calls.
    candidate_limit = max(MAX_FEED_ITEMS, MAX_FEED_ITEMS * 2)
    max_groq_calls = max(1, int(os.getenv("MAX_GROQ_CALLS_PER_RUN", "12")))
    selected = _unique_findings(groups, candidate_limit)
    print(f"findings_selected={len(selected)}")
    print(f"findings_delivery_target={MAX_FEED_ITEMS}")
    print(f"findings_candidate_buffer={candidate_limit}")
    if not selected:
        print("findings_sent=0")
        return

    source_counts = {}
    delivered_items = []
    groq_unavailable = False
    groq_calls = 0
    for item in selected:
        if len(delivered_items) >= MAX_FEED_ITEMS:
            break
        source = item.get("source", "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
        if not groq_unavailable and groq_calls >= max_groq_calls:
            groq_unavailable = True
            print(f"groq_call_budget_reached={max_groq_calls}; using low-token fallback for remaining candidates")
        try:
            if groq_unavailable:
                message = _quota_fallback_finding(item)
            else:
                groq_calls += 1
                message = _format_finding(item)
        except GroqQuotaExhaustedError as exc:
            print(f"ai_writing_stopped={exc}; switching to clearly attributed source briefs")
            groq_unavailable = True
            message = _quota_fallback_finding(item)
        except Exception as exc:
            # Never degrade into raw reposts: skip when Groq cannot produce analysis.
            print(f"ai_writing_error={item['id']}: {exc}")
            continue
        if message is None and (groq_unavailable or editorial_module.GROQ_DAILY_QUOTA_EXHAUSTED):
            groq_unavailable = True
            message = _quota_fallback_finding(item)
        if message is None:
            print(f"editorial_gate_skip={item['id']}: no substantive finding in available source material")
            continue
        try:
            delivered = send_message(message, dry_run=not args.telegram or args.test)
        except Exception as exc:
            print(f"delivery_error={item['id']}: {exc}")
            continue
        if delivered:
            item["_delivered_text"] = message
            delivered_items.append(item)

    if delivered_items:
        mark_sent(delivered_items)
    print(f"selected_source_counts={source_counts}")
    print(f"groq_calls_attempted={groq_calls}")
    print(f"groq_call_budget={max_groq_calls}")
    print(f"findings_sent={len(delivered_items)}")


if __name__ == "__main__":
    main()
