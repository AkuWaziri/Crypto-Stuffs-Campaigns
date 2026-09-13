from __future__ import annotations

import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from collector import RawPost
from models import SourceAccount


FEEDS = {
    "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph": "https://cointelegraph.com/rss",
    "decrypt": "https://decrypt.co/feed",
    "cryptoslate": "https://cryptoslate.com/feed/",
    "bitcoinmagazine": "https://bitcoinmagazine.com/.rss/full/",
    "thedefiant": "https://thedefiant.io/feed",
    "reddit_cryptocurrency": "https://www.reddit.com/r/CryptoCurrency/.rss",
    "reddit_bitcoin": "https://www.reddit.com/r/Bitcoin/.rss",
    "reddit_ethereum": "https://www.reddit.com/r/ethereum/.rss",
    "reddit_solana": "https://www.reddit.com/r/solana/.rss",
    "reddit_defi": "https://www.reddit.com/r/DeFi/.rss",
    "reddit_ethfinance": "https://www.reddit.com/r/ethfinance/.rss",
    "reddit_ethtrader": "https://www.reddit.com/r/ethtrader/.rss",
    "reddit_cryptomarkets": "https://www.reddit.com/r/CryptoMarkets/.rss",
    "ethereum_blog": "https://blog.ethereum.org/feed.xml",
    "solana_news": "https://solana.com/news/rss.xml",
    "uniswap_blog": "https://blog.uniswap.org/rss.xml",
}


class RSSProviderError(RuntimeError):
    pass


def _strip(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"<[^>]+>", " ", value).strip()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        pass

    from email.utils import parsedate_to_datetime

    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _text(element: ET.Element, names: tuple[str, ...]) -> str:
    for child in element:
        tag = child.tag.rsplit("}", 1)[-1].lower()
        if tag in names:
            return _strip(child.text)
    return ""


def _link(element: ET.Element) -> str:
    for child in element:
        tag = child.tag.rsplit("}", 1)[-1].lower()
        if tag == "link":
            href = child.attrib.get("href")
            if href:
                return href.strip()
            if child.text:
                return child.text.strip()
    return ""


def _items(root: ET.Element) -> list[ET.Element]:
    return [element for element in root.iter() if element.tag.rsplit("}", 1)[-1].lower() in {"item", "entry"}]


def _parse_feed(payload: bytes, source: SourceAccount) -> list[RawPost]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise RSSProviderError(f"invalid RSS/XML from {source.handle}") from exc

    posts: list[RawPost] = []
    for item in _items(root):
        title = _text(item, ("title",))
        description = _text(item, ("description", "summary", "content"))
        published = _text(item, ("pubdate", "published", "updated", "date"))
        link = _link(item)
        published_at = _parse_datetime(published)
        if not title or not link or published_at is None:
            continue
        text = title if not description else f"{title} — {description[:800]}"
        posts.append(
            RawPost(
                signal_id=f"rss-{source.handle}-{abs(hash(link))}",
                text=text,
                url=link,
                published_at=published_at,
                engagement=0,
            )
        )
    return posts


class CryptoRSSProvider:
    def __init__(self, feeds: dict[str, str] | None = None, timeout: int = 20):
        self.feeds = feeds or FEEDS
        self.timeout = timeout

    def recent_posts(self, source: SourceAccount, *, since: datetime) -> list[RawPost]:
        url = self.feeds.get(source.handle)
        if not url:
            raise RSSProviderError(f"no RSS feed configured for {source.handle}")
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
                "User-Agent": "TrendsBot/0.3 (read-only crypto trend intelligence)",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RSSProviderError(f"RSS request failed for {source.handle}: {exc}") from exc

        return [post for post in _parse_feed(payload, source) if post.published_at >= since]


class StaticRSSProvider:
    """Small deterministic provider for unit tests."""

    def __init__(self, posts: dict[str, list[RawPost]]):
        self.posts = posts

    def recent_posts(self, source: SourceAccount, *, since: datetime) -> list[RawPost]:
        return [post for post in self.posts.get(source.handle, []) if post.published_at >= since]
