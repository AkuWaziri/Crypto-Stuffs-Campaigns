from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote
import re
import xml.etree.ElementTree as ET
import requests

from config import USER_AGENT
from high_performance import _load_seen_ids, _item_key

MAX_DISCOVERY_ITEMS = 30
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/json, */*"}

QUERIES = (
    "crypto exploit security incident funds stolen",
    "onchain investigation wallet cluster token flows",
    "crypto protocol launch product release",
    "crypto developer tools open source GitHub",
    "DeFi stablecoin payments adoption",
    "crypto airdrop allocation claim analysis",
    "crypto AI agents infrastructure",
    "crypto governance compensation user losses",
    "memecoin launch wallet cluster rug pull analysis",
    "blockchain research findings onchain data",
    "bridge exploit attacker fund movements",
    "crypto builders new feature testnet mainnet",
    "crypto privacy coin unusual transactions",
    "smart contract vulnerability postmortem",
    "crypto exchange hack recovery victims",
)
USEFUL = re.compile(
    r"exploit|hack|security|wallet|on.?chain|transaction|fund flow|airdrop|allocation|"
    r"claim|stablecoin|payment|agent|infrastructure|release|launch|tool|github|open.source|"
    r"research|finding|postmortem|vulnerability|governance|adoption|bridge|memecoin|"
    r"rug.pull|liquidity|protocol|builder|testnet|mainnet|privacy|exchange|victim|"
    r"compensation|recovery|token|defi|smart.contract",
    re.I,
)


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
            "title": title, "text": text[:2200], "url": url,
            "created_at": created.isoformat(), "niche": "crypto findings",
            "tier": "FINDING", "views": 0}


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
                if link and created and created >= cutoff and USEFUL.search(f"{title} {description}"):
                    found.append(_record("news", "news outlet", title, description, link, created))
        except Exception as exc:
            print(f"news_error={query}: {exc}")
    return found


def _github(cutoff):
    found = []
    headers = {**HEADERS, "Accept": "application/vnd.github+json"}
    for query in ("web3 developer tools", "defi analytics", "solidity security tools",
                  "crypto automation", "onchain analytics", "web3 AI agents",
                  "blockchain infrastructure", "crypto security research"):
        try:
            response = requests.get(
                "https://api.github.com/search/repositories",
                params={"q": f"{query} pushed:>{cutoff.strftime('%Y-%m-%d')}",
                        "sort": "updated", "order": "desc", "per_page": 10},
                headers=headers, timeout=15,
            )
            response.raise_for_status()
            for repo in response.json().get("items", []):
                created = _date(repo.get("pushed_at") or repo.get("updated_at"))
                title = repo.get("full_name", "")
                description = repo.get("description", "") or ""
                if created and created >= cutoff and USEFUL.search(f"{title} {description}"):
                    details = f"{description}. Stars: {repo.get('stargazers_count', 0)}"
                    found.append(_record("github", title, title, details, repo.get("html_url", ""), created))
        except Exception as exc:
            print(f"github_error={query}: {exc}")
    return found


def search_crypto_alpha():
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    sent = _load_seen_ids()
    candidates = _google_news(cutoff) + _github(cutoff)
    unique = {}
    for item in candidates:
        if item["id"] in sent or _item_key(item) in sent or not item["url"]:
            continue
        unique[item["url"]] = item
    def rank(item):
        text = item["text"].lower()
        score = sum(2 for term in (
            "exploit", "security", "onchain", "wallet", "research", "finding", "tool",
            "open source", "github", "stablecoin", "payments", "adoption", "airdrop",
            "postmortem", "fund flow", "vulnerability", "compensation", "release",
        ) if term in text)
        return (score, item["created_at"])
    results = sorted(unique.values(), key=rank, reverse=True)
    print(f"crypto_finding_candidates={len(candidates)}")
    print(f"crypto_finding_unique_new={len(results)}")
    return results[:MAX_DISCOVERY_ITEMS]
