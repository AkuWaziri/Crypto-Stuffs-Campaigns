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
    '"crypto exploit" postmortem onchain analysis',
    'DeFi protocol fees revenue TVL users transactions',
    'stablecoin payments settlement volume adoption',
    'crypto AI agents transactions deployment framework',
    'NFT utility market activity volume protocol',
    'crypto security vulnerability disclosure patch',
    'blockchain protocol upgrade mainnet launch metrics',
    'onchain wallet flows token supply accumulation',
    'crypto bridge transfers exploit funds recovery',
    'DePIN network usage revenue device growth',
    'Ethereum L2 transaction fees throughput adoption',
    'Solana protocol launch onchain activity metrics',
    'crypto payment API SDK developer integration',
    'account abstraction smart wallet usage data',
    'real world assets tokenized value onchain',
    'crypto protocol governance tokenomics change',
    'zero knowledge proof infrastructure development',
    'DeFi liquidation lending borrow utilization',
    'stablecoin mint burn supply change',
    'crypto infrastructure product release builder tools',
    'NFT smart contract royalty marketplace change',
    'crypto exploit funds movement wallet analysis',
    'blockchain network active addresses transactions growth',
    'crypto project user growth retention metrics',
    'web3 product build technical demo launch',
    'crypto payments merchant integration settlement',
    'cross chain bridge liquidity flows',
    'crypto hack bounty bug fix security audit',
)
USEFUL = re.compile(
    r'exploit|hack|postmortem|vulnerab|security|on.chain|wallet|transaction|'
    r'volume|fees|revenue|tvl|payment|stablecoin|agent|ai|nft|defi|launch|'
    r'release|upgrade|mainnet|testnet|adoption|users|growth|liquidity|bridge|'
    r'settlement|protocol|infrastructure|developer|sdk|api|open.source|build|'
    r'builder|tokeniz|governance|metrics|funds|recovery|activity|throughput|'
    r'account abstraction|proof|marketplace|mint|burn', re.I,
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
            "text": text[:5000], "url": url, "created_at": created.isoformat(),
            "niche": "crypto research, incidents, metrics and builds",
            "tier": "RESEARCH FINDING", "views": 0}


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
        if item["id"] not in sent and _item_key(item) not in sent and item["url"]:
            unique[item["url"]] = item

    def rank(item):
        text = item["text"].lower()
        terms = (
            "exploit", "postmortem", "on-chain", "wallet", "transaction", "volume",
            "fees", "revenue", "tvl", "payment", "stablecoin", "agent", "nft", "defi",
            "launch", "release", "upgrade", "adoption", "users", "growth", "liquidity",
            "bridge", "settlement", "metrics", "funds", "recovery", "security", "audit",
            "mainnet", "sdk", "api",
        )
        score = sum(3 for term in terms if term in text)
        if re.search(r'\d[\d,.]*\s?(%|million|billion|thousand|usd|\$|eth|btc)', text):
            score += 4
        if len(text) > 350:
            score += 2
        return score, item["created_at"]

    results = sorted(unique.values(), key=rank, reverse=True)
    print(f"crypto_web_candidates={len(candidates)}")
    print(f"crypto_web_unique_new={len(results)}")
    return results[:MAX_DISCOVERY_ITEMS]
