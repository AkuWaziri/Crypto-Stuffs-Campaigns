from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import quote, urljoin
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from config import USER_AGENT, REDDIT_SUBREDDITS, MEDIUM_TAGS, TELEGRAM_CHANNELS, BLUESKY_QUERIES

# Research-led searches rather than meme/satire discovery.
CONTENT_QUERIES = (
    "crypto exploit postmortem root cause funds recovered",
    "DeFi protocol exploit onchain analysis",
    "smart contract vulnerability security disclosure",
    "onchain wallet flows unusual accumulation",
    "stablecoin payment volume adoption settlement",
    "crypto payments merchant integration",
    "AI agents onchain transactions crypto",
    "crypto AI agent framework deployment",
    "DeFi TVL fees revenue protocol metrics",
    "DEX volume liquidity changes onchain",
    "bridge exploit cross chain transfers",
    "NFT market volume royalties utility launch",
    "crypto protocol upgrade technical release",
    "blockchain developer tools SDK API release",
    "open source crypto build demo",
    "testnet mainnet launch ecosystem adoption",
    "account abstraction wallet adoption",
    "real world assets tokenization onchain data",
    "DePIN network usage revenue devices",
    "L2 transaction fees throughput activity",
    "crypto governance proposal token economics",
    "crypto security incident timeline",
    "crypto project product usage numbers",
    "stablecoin supply mint burn flow analysis",
    "crypto funding product launch technical details",
    "Solana onchain activity protocol launch",
    "Ethereum ecosystem development metrics",
    "zero knowledge proof infrastructure release",
    "crypto protocol fees users transactions",
    "blockchain payments settlement infrastructure",
)

HEADERS = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/json,application/xml"}


def _clean(text):
    raw = unescape(str(text or ""))
    soup = BeautifulSoup(raw, "html.parser")
    for node in soup(["script", "style", "noscript"]):
        node.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def _now():
    return datetime.now(timezone.utc).isoformat()


def _item(source, author, text, url, created_at=None, crypto_query=False):
    return {"id": f"{source}:{url or text[:100]}", "author": author or source,
            "text": _clean(text), "url": url, "created_at": created_at or _now(),
            "source": source, "crypto_query": crypto_query}


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
        title = _clean(node.findtext("title", ""))
        description = _clean(node.findtext("description", ""))
        link = _clean(node.findtext("link", ""))
        pub = _parse_date(node.findtext("pubDate", ""))
        author = node.findtext("{http://purl.org/dc/elements/1.1/}creator", "") or source
        text = title
        if description and description.casefold() not in title.casefold():
            text = f"{title}. {description}" if title else description
        items.append(_item(source, author, text, link, pub, True))
    return items


def _reddit():
    items = []
    for subreddit in REDDIT_SUBREDDITS:
        for query in CONTENT_QUERIES:
            url = f"https://www.reddit.com/r/{quote(subreddit)}/search.json?q={quote(query)}&restrict_sr=1&sort=new&t=month&limit=15"
            try:
                response = requests.get(url, headers=HEADERS, timeout=20)
                response.raise_for_status()
                data = response.json()
                for child in data.get("data", {}).get("children", []):
                    post = child.get("data", {})
                    permalink = post.get("permalink", "")
                    if not permalink:
                        continue
                    created = datetime.fromtimestamp(post["created_utc"], timezone.utc).isoformat() if post.get("created_utc") else None
                    items.append(_item("reddit", post.get("author") or subreddit,
                                       f"{post.get('title', '')} {post.get('selftext', '')}",
                                       urljoin("https://www.reddit.com", permalink), created, True))
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


def _farcaster():
    items = []
    for query in CONTENT_QUERIES:
        url = "https://api.warpcast.com/v2/search-casts?q=" + quote(query) + "&limit=30"
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            data = response.json()
            casts = data.get("result", {}).get("casts", []) if isinstance(data, dict) else []
            for cast in casts:
                text = cast.get("text", "")
                if not text:
                    continue
                author_obj = cast.get("author") or {}
                author = author_obj.get("username") or author_obj.get("display_name") or "farcaster"
                cast_url = cast.get("url") or cast.get("hash")
                if cast_url and not str(cast_url).startswith("http"):
                    username = author_obj.get("username", "farcaster")
                    cast_url = f"https://warpcast.com/{username}/{str(cast_url).removeprefix('0x')}"
                created = cast.get("timestamp") or cast.get("created_at")
                items.append(_item("farcaster", author, text, cast_url, created, True))
        except Exception as exc:
            print(f"farcaster_error={query}: {exc}")
    return items


def _bluesky():
    items = []
    for query in BLUESKY_QUERIES:
        url = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?q=" + quote(query) + "&limit=30"
        try:
            response = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=20)
            response.raise_for_status()
            for post in response.json().get("posts", []):
                record = post.get("record", {})
                author = post.get("author", {}).get("handle", "bluesky")
                text = record.get("text", "")
                uri = post.get("uri", "")
                rkey = uri.rsplit("/", 1)[-1]
                items.append(_item("bluesky", author, text, f"https://bsky.app/profile/{author}/post/{rkey}", record.get("createdAt"), True))
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
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def fetch_public_campaigns():
    return fetch_public_content()
