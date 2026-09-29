from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote, urljoin
import re
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from config import (
    USER_AGENT,
    REDDIT_SUBREDDITS,
    MEDIUM_TAGS,
    TELEGRAM_CHANNELS,
    BLUESKY_QUERIES,
)

CONTENT_QUERIES = (
    # Campaigns / opportunities
    "crypto campaign", "web3 campaign", "crypto rewards", "web3 rewards",
    "crypto contest", "web3 contest", "crypto competition",
    "crypto hackathon", "web3 hackathon", "crypto buildathon",
    "crypto bounty", "web3 bounty", "crypto grants", "web3 grants",
    "crypto creator campaign", "web3 creator campaign",
    "crypto video contest", "web3 video contest", "crypto video challenge",
    "crypto art contest", "web3 design contest", "crypto meme contest",
    "crypto writing contest", "crypto content contest", "crypto research bounty",
    "crypto ambassador program", "web3 ambassador", "crypto community challenge",
    "crypto testnet rewards", "crypto devnet rewards",
    "crypto trading competition", "crypto trading contest",
    "crypto NFT campaign", "crypto token rewards", "crypto points campaign",
    "crypto airdrop", "crypto quests", "crypto missions",
    "crypto idea competition", "web3 innovation challenge", "crypto pitch competition",
    # Humor / culture
    "crypto satire", "crypto ironic", "crypto funny", "crypto meme",
    "crypto comic", "crypto metaphor",
    # Research / findings
    "crypto research", "crypto findings", "crypto discovery",
    "crypto investigation", "crypto experiment", "crypto analysis",
    # Building / ideas
    "crypto building", "crypto builders", "crypto prototype",
    "crypto idea", "crypto ideas", "crypto product", "crypto app",
    "protocol idea", "crypto use case", "crypto problem",
    # Technical / open source
    "crypto architecture", "crypto infrastructure", "crypto technical",
    "crypto open source", "crypto SDK", "crypto developer", "crypto integration",
    # Applications
    "crypto payments", "crypto identity", "crypto gaming", "crypto social",
    "crypto creator", "crypto AI", "crypto DePIN", "crypto commerce",
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
        return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        return value

def _rss(url, source):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    items = []
    for node in root.findall(".//item"):
        title = node.findtext("title", "")
        description = node.findtext("description", "")
        link = node.findtext("link", "")
        pub = _parse_date(node.findtext("pubDate", ""))
        author = node.findtext("{http://purl.org/dc/elements/1.1/}creator", "") or source
        items.append(_item(source, author, f"{title} {description}", link, pub, True))
    return items

def _reddit():
    items = []
    for subreddit in REDDIT_SUBREDDITS:
        for query in CONTENT_QUERIES:
            url = (
                f"https://www.reddit.com/r/{quote(subreddit)}/search.json"
                f"?q={quote(query)}&restrict_sr=1&sort=new&t=month&limit=25"
            )
            try:
                response = requests.get(url, headers=HEADERS, timeout=20)
                response.raise_for_status()
                data = response.json()
                for child in data.get("data", {}).get("children", []):
                    post = child.get("data", {})
                    permalink = post.get("permalink", "")
                    if not permalink:
                        continue
                    created = (
                        datetime.fromtimestamp(post["created_utc"], timezone.utc).isoformat()
                        if post.get("created_utc") else None
                    )
                    items.append(_item(
                        "reddit",
                        post.get("author") or subreddit,
                        f"{post.get('title', '')} {post.get('selftext', '')}",
                        urljoin("https://www.reddit.com", permalink),
                        created,
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
            soup = BeautifulSoup(response.text, "html.parser")
            for message in soup.select(".tgme_widget_message"):
                text_node = message.select_one(".tgme_widget_message_text")
                if not text_node:
                    continue
                text = text_node.get_text(" ", strip=True)
                date_node = message.select_one(".tgme_widget_message_date")
                link = date_node.get("href") if date_node else url
                time_node = date_node.find("time") if date_node else None
                created = time_node.get("datetime") if time_node else None
                items.append(_item("telegram", f"@{channel}", text, link, created, True))
        except Exception as exc:
            print(f"telegram_error={channel}: {exc}")
    return items

def _bluesky():
    items = []
    for query in BLUESKY_QUERIES:
        url = (
            "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
            "?q=" + quote(query) + "&limit=50"
        )
        try:
            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                timeout=20,
            )
            response.raise_for_status()
            for post in response.json().get("posts", []):
                record = post.get("record", {})
                author = post.get("author", {}).get("handle", "bluesky")
                text = record.get("text", "")
                uri = post.get("uri", "")
                rkey = uri.rsplit("/", 1)[-1]
                url_out = f"https://bsky.app/profile/{author}/post/{rkey}"
                items.append(_item(
                    "bluesky", author, text, url_out, record.get("createdAt"), True
                ))
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

def fetch_public_campaigns():
    return fetch_public_content()
