from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote
import re
import xml.etree.ElementTree as ET
import requests

from config import USER_AGENT
from high_performance import _load_seen_ids, _item_key

MAX_DISCOVERY_ITEMS = 15
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/json, */*"}
QUERIES = (
    "crypto developer tools GitHub",
    "DeFi guide tutorial checklist",
    "Solidity security research tools",
    "crypto automation workflow",
    "onchain analytics dashboard",
    "crypto AI agent framework",
    "web3 hackathon builder resources",
    "crypto API open source",
    "blockchain infrastructure release",
    "stablecoin payments developer",
    "crypto research findings",
    "Ethereum developer guide",
)
USEFUL = re.compile(r"guide|tutorial|how to|step.by.step|checklist|tool|github|open.source|repo|workflow|automation|prompt|framework|sdk|api|dashboard|research|finding|security|hackathon|build|builder|launch|release|testnet|onchain|solidity|smart contract|defi|wallet|bridge|agent|infrastructure|payments|stablecoin|protocol|data|free", re.I)

def _date(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    except (TypeError, ValueError):
        try:
            dt = parsedate_to_datetime(str(value))
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            return None

def _record(source, author, title, description, url, created):
    text = " ".join(f"{title} {description}".split())
    return {"id": f"{source}:{url}", "source": source, "author": author or source,
            "text": text[:900], "url": url, "created_at": created.isoformat(),
            "niche": "guides, tools and builds", "tier": "CRYPTO ALPHA", "views": 0}

def _google_news(cutoff):
    found = []
    for query in QUERIES:
        url = "https://news.google.com/rss/search?q=" + quote(query + " when:7d") + "&hl=en-US&gl=US&ceid=US:en"
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            for node in root.findall(".//item"):
                title = node.findtext("title", "")
                link = node.findtext("link", "")
                created = _date(node.findtext("pubDate", ""))
                desc_node = node.find("description")
                description = "".join(desc_node.itertext()) if desc_node is not None else ""
                text = f"{title} {description}"
                if link and created and created >= cutoff and USEFUL.search(text):
                    found.append(_record("web", "web discovery", title, description, link, created))
        except Exception as exc:
            print(f"alpha_web_error={query}: {exc}")
    return found

def search_crypto_alpha():
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    sent = _load_seen_ids()
    candidates = _google_news(cutoff)
    unique = {}
    for item in candidates:
        if item["id"] in sent or _item_key(item) in sent or not item["url"]:
            continue
        unique[item["url"]] = item
    def rank(item):
        text = item["text"].lower()
        score = sum(2 for term in ("github", "open source", "tutorial", "checklist", "workflow", "tool", "guide", "research", "security", "dashboard", "api", "framework") if term in text)
        return (score, item["created_at"])
    results = sorted(unique.values(), key=rank, reverse=True)
    print(f"crypto_alpha_candidates={len(candidates)}")
    print(f"crypto_alpha_unique_new={len(results)}")
    return results[:MAX_DISCOVERY_ITEMS]
