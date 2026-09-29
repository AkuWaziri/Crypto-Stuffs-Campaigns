from datetime import datetime, timezone
from urllib.parse import quote, urljoin
import json
import re
import xml.etree.ElementTree as ET

import requests

from config import (
    USER_AGENT,
    REDDIT_SUBREDDITS,
    MEDIUM_TAGS,
    TELEGRAM_CHANNELS,
    BLUESKY_QUERIES,
)

HEADERS = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/json,application/xml"}

CONTENT_QUERIES = (
    "crypto satire", "crypto ironic", "crypto funny", "crypto meme",
    "crypto comic", "crypto metaphor", "crypto research", "crypto findings",
    "crypto discovery", "crypto investigation",
)

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

def _rss(url, source):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    items = []
    for node in root.findall(".//item"):
        title = node.findtext("title", "")
        description = node.findtext("description", "")
        link = node.findtext("link", "")
        pub = node.findtext("pubDate", "")
        author = node.findtext("{http://purl.org/dc/elements/1.1/}creator", "") or source
        items.append(_item(source, author, f"{title} {description}", link, pub, True))
    return items

def _reddit():
    items = []
    for subreddit in REDDIT_SUBREDDITS:
        for query in CONTENT_QUERIES:
            url = f"https://www.reddit.com/r/{quote(subreddit)}/search.json?q={quote(query)}&restrict_sr=1&sort=new&t=month&limit=25"
            try:
                response = requests.get(url, headers=HEADERS, timeout=20)
                response.raise_for_status()
                data = response.json()
                for child in data.get("data", {}).get("children", []):
                    post = child.get("data", {})
                    permalink = post.get("permalink", "")
                    if not permalink:
                        continue
                    items.append(_item(
                        "reddit",
                        post.get("author") or subreddit,
                        f"{post.get('title', '')} {post.get('selftext', '')}",
                        urljoin("https://www.reddit.com", permalink),
                        datetime.fromtimestamp(post["created_utc"], timezone.utc).isoformat() if post.get("created_utc") else None,
                        True,
                    ))
            except Exception as exc:
                print(f"reddit_error={subreddit}:{query}: {exc}")
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
            html = response.text
            for match in re.finditer(
                r'<div class="tgme_widget_message_wrap.*?</div>\\s*</div>\\s*</div>',
                html, re.S,
            ):
                block = match.group(0)
                text_match = re.search(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', block, re.S)
                if not text_match:
                    continue
                text = re.sub(r"<br\\s*/?>", "\\n", text_match.group(1))
                text = re.sub(r"<[^>]+>", " ", text)
                link_match = re.search(r'href="(https://t.me/[^"]+)"[^>]*class="tgme_widget_message_date"', block)
                link = link_match.group(1) if link_match else url
                items.append(_item("telegram", f"@{channel}", text, link, None, True))
        except Exception as exc:
            print(f"telegram_error={channel}: {exc}")
    return items

def _bluesky():
    items = []
    for query in BLUESKY_QUERIES:
        url = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?q=" + quote(query) + "&limit=50"
        try:
            response = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=20)
            response.raise_for_status()
            for post in response.json().get("posts", []):
                record = post.get("record", {})
                author = post.get("author", {}).get("handle", "bluesky")
                text = record.get("text", "")
                uri = post.get("uri", "")
                rkey = uri.rsplit("/", 1)[-1]
                url_out = f"https://bsky.app/profile/{author}/post/{rkey}"
                created = record.get("createdAt")
                items.append(_item("bluesky", author, text, url_out, created, True))
        except Exception as exc:
            print(f"bluesky_error={query}: {exc}")
    return items

def fetch_public_content():
    items = []
    for tag in MEDIUM_TAGS:
        url = f"https://medium.com/feed/tag/{quote(tag)}"
        try:
            found = _rss(url, "medium")
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

    unique, seen = [], set()
    for item in items:
        key = item.get("url") or item.get("id")
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique

# Backward-compatible name for callers that still import the old function.
def fetch_public_campaigns():
    return fetch_public_content()
