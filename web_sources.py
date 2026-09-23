from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import USER_AGENT

SOURCES = [
    ("zealy", "https://www.zealy.io/earn"),
    ("galxe", "https://app.galxe.com/quest/explore/all"),
    ("layer3", "https://app.layer3.xyz/"),
    ("airdrops_io", "https://airdrops.io/latest/"),
    ("airdropalert", "https://airdropalert.com/farm/"),
]

KEYWORDS = (
    "airdrop", "points", "quest", "campaign", "reward", "rewards",
    "testnet", "mainnet", "devnet", "mint", "nft", "token sale",
    "ido", "public sale", "contest", "bounty", "grant", "ambassador",
    "hackathon", "earn", "ongoing", "active", "confirmed",
)

BAD_TEXT = {
    "home", "explore", "search", "login", "sign up", "learn more",
    "all", "about", "contact", "privacy", "terms", "follow",
}

def _clean(text):
    return " ".join(text.split())

def _candidate_from_link(source, base_url, link):
    text = _clean(link.get_text(" ", strip=True))
    href = link.get("href")
    if not href:
        return None

    url = urljoin(base_url, href)
    low = text.lower()

    if not text or len(text) < 3 or text.lower() in BAD_TEXT:
        return None
    if len(text) > 240:
        text = text[:237] + "..."

    parent_text = _clean(link.parent.get_text(" ", strip=True)) if link.parent else ""
    combined = f"{text} {parent_text}".strip()

    # Campaign pages are more useful than navigation. Require a campaign/reward
    # signal in the visible card text or title.
    if not any(word in combined.lower() for word in KEYWORDS):
        return None

    return {
        "id": f"web:{source}:{url}",
        "author": source,
        "text": combined[:1800],
        "url": url,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
    }

def _extract_links(source, base_url, html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    seen = set()

    for link in soup.find_all("a", href=True):
        item = _candidate_from_link(source, base_url, link)
        if not item:
            continue

        key = item["url"]
        if key in seen:
            continue
        seen.add(key)
        items.append(item)

    return items

def _fetch_source(source, url):
    response = requests.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
        timeout=20,
    )
    response.raise_for_status()

    items = _extract_links(source, url, response.text)

    # If a source exposes no individual cards in server-rendered HTML, don't
    # send its entire navigation shell as a fake campaign.
    return items

def fetch_public_campaigns():
    items = []

    for source, url in SOURCES:
        try:
            found = _fetch_source(source, url)
            items.extend(found)
            print(f"web_source={source} items={len(found)}")
        except Exception as exc:
            print(f"web_source_error={source}: {exc}")

    # Deduplicate identical campaign URLs across providers.
    unique = []
    seen_urls = set()
    for item in items:
        url = item.get("url")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        unique.append(item)

    return unique
