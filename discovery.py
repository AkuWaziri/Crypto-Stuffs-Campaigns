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


# A separate professional-positioning research lane. These are not generic job
# listings: they seek technical evidence and product mechanics that can become
# original, useful public posts demonstrating the owner's skill lenses.
SKILL_RESEARCH_QUERIES = (
    ("motion_video_creator", '"web3 protocol" product launch visual explainer video design brief OR blog'),
    ("motion_video_creator", 'crypto protocol docs mechanism product launch visual storytelling motion design'),
    ("web3_compliance", 'site:esma.europa.eu crypto assets MiCA guidance stablecoin compliance'),
    ("web3_compliance", 'crypto compliance travel rule sanctions stablecoin official guidance analysis'),
    ("web3_compliance", 'web3 compliance protocol risk controls regulatory blog research'),
    ("bug_bounty", 'web3 bug bounty smart contract vulnerability disclosure postmortem security research'),
    ("bug_bounty", 'DeFi protocol audit report exploit root cause remediation bug bounty'),
    ("bug_bounty", 'smart contract security research attack vector mitigation technical blog'),
    ("points_campaign_designer", 'crypto protocol points program rules eligibility referral sybil docs'),
    ("points_campaign_designer", 'web3 referral campaign points incentives token allocation official blog'),
    ("points_campaign_designer", 'crypto points program changes reward mechanics campaign analysis'),
    ("reputation_manager", 'web3 contributor reputation scoring governance participation docs'),
    ("reputation_manager", 'crypto protocol ambassador contributor program reputation community blog'),
    ("reputation_manager", 'DAO governance participation reputation incentives research'),
)



# A dedicated how-to/research lane: practical, free-first guides that readers can
# reproduce. Search broadly across protocols and tooling, but prefer official
# docs, primary sources and guides that link to the actual product/documentation.
HOWTO_RESEARCH_QUERIES = (
    '"how to" DeFi guide free tools protocol docs',
    'Starknet meme coins how to trade launchpad DEX aggregator official guide',
    'free AI API credits startup program eligibility official documentation',
    'free VPS cloud credits always free tier setup guide official docs',
    'crypto multisig wallet setup Safe Squads official guide',
    'free crypto security tools wallet approval revoke phishing prevention guide',
    'Bitcoin mining profitability setup electricity pool guide educational',
    'DeFi lending borrowing liquidity staking how it works risks official docs',
    'crypto trading order types slippage limit orders risk management guide',
    'X tools automation analytics API free tier guide official documentation',
    'free open source crypto research on-chain analytics dashboards tutorial',
    'free cloud GPU credits AI inference models developer program official',
    'crypto airdrop points campaign eligibility anti sybil how to guide',
    'self hosted node RPC indexer crypto VPS deployment tutorial',
    'smart contract testnet deploy verify contract free tutorial',
    'open source security bug bounty responsible disclosure how to guide',
    'free email domain setup SPF DKIM MX startup credits guide',
    'free developer tools rate limits API keys credits eligibility guide',
)
HOWTO_SIGNAL = re.compile(
    r'how to|step.by.step|tutorial|guide|walkthrough|setup|set up|configure|'
    r'getting started|documentation|docs|free tier|free credits|no.cost|open.source|'
    r'free tool|testnet|multisig|slippage|launchpad|aggregator|vps|cloud credits|'
    r'bug bounty|security|wallet|defi|trading|mining|api|deployment|deploy',
    re.I,
)


def search_howto_research():
    """Discover practical, free-first tutorials and retain their reference URLs."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    found = []
    seen_urls = set()
    for query in HOWTO_RESEARCH_QUERIES:
        url = (
            "https://news.google.com/rss/search?q="
            + quote(query + " when:7d")
            + "&hl=en-US&gl=US&ceid=US:en"
        )
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
                combined = f"{title} {description}"
                if not link or link in seen_urls or not created or created < cutoff:
                    continue
                if not HOWTO_SIGNAL.search(combined):
                    continue
                # Prefer actionable material with an explicit free/open-source/credits
                # signal; still permit genuinely useful setup/security guides.
                free_signal = re.search(
                    r'free|zero.cost|no.cost|open.source|credits|free tier|testnet',
                    combined, re.I,
                )
                practical_signal = re.search(
                    r'how to|tutorial|guide|walkthrough|setup|set up|getting started|'
                    r'documentation|docs|step.by.step|configure|deploy',
                    combined, re.I,
                )
                if not (free_signal and practical_signal):
                    continue
                seen_urls.add(link)
                item = _record(
                    "howto_research",
                    "web research",
                    title,
                    description,
                    link,
                    created,
                )
                item["content_lane"] = "research_guides"
                item["niche"] = "practical free-first guides: DeFi, security, AI credits, VPS, trading, mining and tools"
                item["tier"] = "HOW-TO RESEARCH"
                found.append(item)
        except Exception as exc:
            print(f"howto_research_error={query}: {exc}")

    sent = _load_seen_ids()
    unique = {}
    for item in found:
        if item["id"] not in sent and _item_key(item) not in sent and item["url"]:
            unique[item["url"]] = item
    results = sorted(unique.values(), key=lambda item: item["created_at"], reverse=True)
    print(f"howto_research_candidates={len(found)}")
    print(f"howto_research_unique_new={len(results)}")
    return results[:20]

def search_skill_showcase():
    """Find source-backed material that can become public skill-showcase posts.

    Uses a wider 30-day window than the breaking-news lane because docs,
    whitepapers, technical blogs and research remain useful beyond one news cycle.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    found = []
    seen_urls = set()
    for profile, query in SKILL_RESEARCH_QUERIES:
        url = (
            "https://news.google.com/rss/search?q="
            + quote(query + " when:30d")
            + "&hl=en-US&gl=US&ceid=US:en"
        )
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
                if not link or link in seen_urls or not created or created < cutoff:
                    continue
                if not USEFUL.search(f"{title} {description}") and len(description.strip()) < 80:
                    continue
                seen_urls.add(link)
                item = _record(
                    "skill_research",
                    "web research",
                    title,
                    description,
                    link,
                    created,
                )
                item["content_lane"] = "skill_showcase"
                item["skill_profile"] = profile
                item["niche"] = f"skill showcase: {profile}; docs, whitepapers, research and blogs"
                item["tier"] = "SKILL SHOWCASE RESEARCH"
                found.append(item)
        except Exception as exc:
            print(f"skill_research_error={profile}:{query}: {exc}")

    sent = _load_seen_ids()
    unique = {}
    for item in found:
        if item["id"] not in sent and _item_key(item) not in sent and item["url"]:
            unique[item["url"]] = item
    results = sorted(unique.values(), key=lambda item: item["created_at"], reverse=True)
    print(f"skill_research_candidates={len(found)}")
    print(f"skill_research_unique_new={len(results)}")
    return results[:20]
