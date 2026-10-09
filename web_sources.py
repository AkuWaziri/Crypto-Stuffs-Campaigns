from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote, urljoin
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from config import USER_AGENT, REDDIT_SUBREDDITS, MEDIUM_TAGS, TELEGRAM_CHANNELS, BLUESKY_QUERIES

CONTENT_QUERIES = (
    "crypto security exploit hack incident",
    "onchain wallet investigation transactions",
    "crypto protocol launch product release",
    "crypto developer tool open source",
    "DeFi stablecoin payments adoption",
    "crypto airdrop allocation claims",
    "crypto AI agent infrastructure",
    "crypto governance controversy compensation",
    "crypto memecoin wallet cluster",
    "blockchain research findings",
    "crypto bridge exploit funds movement",
    "crypto builders new feature",
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/json,application/xml",
}


def _clean(text):
    return " ".join(str(text or "").split())


def _now():
    return datetime.now(timezone.utc).isoformat()


def _item(source, author, text, url, created_at=None, crypto_query=False):
    return {
        "id": f"{source}:{url or text[:100]}",
        "author": author or source,
        "text": _clean(text),
        "url": url,
        "created_at": created_at or _now(),
        "source": source,
        "crypto_query": crypto_query,
    }


def _parse_date(value):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        return value


def _rss(url, source):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    items = []
    for node in root.findall(".//item"):
        title = node.findtext("title", "")
        description_node = node.find("description")
        description = "".join(description_node.itertext()) if description_node is not None else ""
        link = node.findtext("link", "")
        pub = _parse_date(node.findtext("pubDate", ""))
        author = node.findtext("{http://purl.org/dc/elements/1.1/}creator", "") or source
        if link:
            items.append(_item(source, author, f"{title} {description}", link, pub, True))
    return items


def _reddit():
    items = []
    for subreddit in REDDIT_SUBREDDITS:
        query = "crypto security exploit findings build research wallet airdrop"
        url = (
            f"https://www.reddit.com/r/{quote(subreddit)}/search.json"
            f"?q={quote(query)}&restrict_sr=1&sort=new&t=week&limit=25"
        )
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            for child in response.json().get("data", {}).get("children", []):
                post = child.get("data", {})
                permalink = post.get("permalink", "")
                if not permalink:
                    continue
                created = datetime.fromtimestamp(post["created_utc"], timezone.utc).isoformat() if post.get("created_utc") else None
                text = f"{post.get('title', '')} {post.get('selftext', '')}"
                items.append(_item("reddit", post.get("author") or subreddit, text,
                                   urljoin("https://www.reddit.com", permalink), created, True))
        except Exception as exc:
            print(f"reddit_error={subreddit}: {exc}")
    return items


def _telegram():
    items = []
    for channel in TELEGRAM_CHANNELS:
        channel = channel.lstrip("@ ").strip().rstrip("/")
        if not channel:
            continue
        url = f"https://t.me/s/{channel}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for message in soup.select(".tgme_widget_message"):
                text_node = message.select_one(".tgme_widget_message_text")
                if not text_node:
                    continue
                date_node = message.select_one(".tgme_widget_message_date")
                link = date_node.get("href") if date_node else url
                time_node = date_node.find("time") if date_node else None
                created = time_node.get("datetime") if time_node else None
                items.append(_item("telegram", f"@{channel}", text_node.get_text(" ", strip=True), link, created, True))
        except Exception as exc:
            print(f"telegram_error={channel}: {exc}")
    return items


def _farcaster():
    items = []
    for query in CONTENT_QUERIES:
        url = "https://api.warpcast.com/v2/search-casts?q=" + quote(query) + "&limit=25"
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            data = response.json()
            casts = data.get("result", {}).get("casts", []) if isinstance(data, dict) else []
            for cast in casts:
                text = cast.get("text", "")
                author_obj = cast.get("author") or {}
                author = author_obj.get("username") or author_obj.get("display_name") or "farcaster"
                cast_url = cast.get("url") or cast.get("hash")
                if cast_url and not str(cast_url).startswith("http"):
                    cast_url = f"https://warpcast.com/{author}/{str(cast_url).replace('0x', '')}"
                created = cast.get("timestamp") or cast.get("created_at")
                if text and cast_url:
                    items.append(_item("farcaster", author, text, cast_url, created, True))
        except Exception as exc:
            print(f"farcaster_error={query}: {exc}")
    return items


def _bluesky():
    items = []
    for query in BLUESKY_QUERIES:
        url = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?q=" + quote(query) + "&limit=30"
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            for post in response.json().get("posts", []):
                record = post.get("record", {})
                author = post.get("author", {}).get("handle", "bluesky")
                text = record.get("text", "")
                uri = post.get("uri", "")
                rkey = uri.rsplit("/", 1)[-1]
                created = record.get("createdAt")
                if text and rkey:
                    items.append(_item("bluesky", author, text, f"https://bsky.app/profile/{author}/post/{rkey}", created, True))
        except Exception as exc:
            print(f"bluesky_error={query}: {exc}")
    return items


def fetch_public_content():
    items = []
    for tag in MEDIUM_TAGS:
        try:
            found = _rss(f"https://medium.com/feed/tag/{quote(tag)}", "medium")
            items.extend(found)
            print(f"medium_source={tag} items={len(found)}")
        except Exception as exc:
            print(f"medium_error={tag}: {exc}")
    if REDDIT_SUBREDDITS:
        found = _reddit()
        items.extend(found)
        print(f"reddit_items={len(found)}")
    if TELEGRAM_CHANNELS:
        found = _telegram()
        items.extend(found)
        print(f"telegram_items={len(found)}")
    if BLUESKY_QUERIES:
        found = _bluesky()
        items.extend(found)
        print(f"bluesky_items={len(found)}")
    found = _farcaster()
    items.extend(found)
    print(f"farcaster_items={len(found)}")

    unique, seen = [], set()
    for item in items:
        key = item.get("url") or item.get("id")
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
