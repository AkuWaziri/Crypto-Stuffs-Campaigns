"""Editorial intelligence helpers for the Crypto-Stuffs-Campaigns feed.

This module ranks discovered items and turns them into clearly labeled research
prompts. It does not invent facts or publish content.
"""
import re

TOPIC_RULES = [
    ("Security", ("exploit", "hack", "vulnerability", "security", "audit", "attack", "drain", "bug bounty")),
    ("Stablecoins & payments", ("stablecoin", "payments", "payment", "usdc", "usdt", "settlement", "remittance")),
    ("DeFi & markets", ("defi", "liquidity", "yield", "lending", "borrow", "dex", "trading", "market")),
    ("AI & agents", (" ai ", "agent", "llm", "model", "automation")),
    ("Developer tools", ("github", "open source", "sdk", "api", "tool", "framework", "repository", "repo", "tutorial", "guide")),
    ("On-chain research", ("onchain", "on-chain", "wallet", "transaction", "contract", "smart contract", "block explorer")),
    ("Infrastructure", ("infrastructure", "node", "layer 2", "l2", "bridge", "scaling", "rpc", "rollup")),
    ("Funding & opportunities", ("grant", "funding", "hackathon", "airdrop", "incentive", "rewards", "points")),
]

TOOL_IDEAS = [
    (("stablecoin", "payment", "remittance"), "Stablecoin route and fee comparator", "Compare transfer cost, settlement time and supported networks from public data."),
    (("security", "exploit", "vulnerability", "audit"), "Contract-change watchlist", "Track verified contract or repository changes and link each alert to its primary source."),
    (("github", "open source", "sdk", "api", "repository", "repo", "framework"), "Developer resource index", "Collect useful repositories with recent activity, a clear use case and setup instructions."),
    (("wallet", "onchain", "on-chain", "transaction", "contract"), "Readable transaction explainer", "Translate public transaction fields and contract calls into a traceable, human-readable walkthrough."),
    (("defi", "liquidity", "yield", "lending"), "Protocol metric comparison", "Compare selected public metrics across protocols while showing timestamps and source links."),
    (("ai", "agent", "automation"), "Agent integration starter kit", "Turn a documented API or agent framework into a small, reproducible working example."),
    (("hackathon", "grant", "funding", "airdrop", "incentive", "rewards"), "Opportunity verification tracker", "Track official eligibility, deadlines and source links, separating confirmed details from rumors."),
]

def _normal(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()

def _has_term(text, term):
    if term in {"ai", "l2", "api", "sdk", "rpc", "dex", "usdc", "usdt"}:
        return re.search(r"\b" + re.escape(term) + r"\b", text) is not None
    return term in text

def _topic(item):
    text = " " + _normal(item.get("text", "")).lower() + " "
    for topic, terms in TOPIC_RULES:
        if any(_has_term(text, term) for term in terms):
            return topic
    return "Crypto research"

def _score(item):
    text = _normal(item.get("text", "")).lower()
    source = str(item.get("source", "")).lower()
    score = 0
    if str(item.get("url", "")).startswith(("https://", "http://")):
        score += 2
    if source in {"github", "web", "x_high_performance"}:
        score += 1
    if any(word in text for word in ("how to", "guide", "tutorial", "open source", "sdk", "api", "research", "finding", "security", "release", "proposal", "data", "benchmark")):
        score += 3
    if any(word in text for word in ("new", "launch", "released", "today", "breaking", "vulnerability", "exploit", "proposal")):
        score += 2
    if len(text) >= 180:
        score += 1
    views = item.get("views", 0)
    if isinstance(views, (int, float)) and views >= 50000:
        score += 1
    return score

def _title(item):
    text = _normal(item.get("text", ""))
    sentence = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0]
    return (sentence or text)[:170].rstrip()

def _tool_idea(item):
    text = _normal(item.get("text", "")).lower()
    for terms, name, description in TOOL_IDEAS:
        if any(_has_term(text, term) for term in terms):
            return name, description
    return "Evidence-linked topic tracker", "Collect primary sources and meaningful updates for this topic, with dates and duplicate detection."

def _research_prompt(item):
    topic = _topic(item)
    source = str(item.get("source", "unknown")).upper()
    url = str(item.get("url", "")).strip()
    views = item.get("views")
    details = f"Topic: {topic} | Source: {source}"
    if isinstance(views, (int, float)) and views > 0:
        details += f" | X views: {views:,}"
    return (
        f"• {topic}: {_title(item)}\n"
        f"  Signal: {details}. Treat the source as a lead; verify the underlying claim.\n"
        f"  Investigate: What changed, what primary evidence supports it, and what remains uncertain?\n"
        f"  Content angle: Explain the specific mechanism or implication, then show the evidence and one practical takeaway.\n"
        f"  Source: {url}"
    )

def build_editorial_digest(items, limit=3):
    """Return a compact Telegram digest of ranked findings and one build opportunity."""
    valid = [item for item in items or [] if isinstance(item, dict) and item.get("url") and item.get("text")]
    if not valid:
        return ""
    ranked = sorted(valid, key=lambda item: (_score(item), int(item.get("views") or 0)), reverse=True)
    chosen = ranked[:max(1, min(int(limit), 5))]
    sections = [
        "EDITORIAL INTELLIGENCE | HUMAN REVIEW REQUIRED",
        "",
        "Highest-priority leads from this run. These are research prompts, not verified conclusions or ready-to-publish claims.",
        "",
    ]
    sections.extend(_research_prompt(item) for item in chosen)
    idea_name, idea_desc = _tool_idea(chosen[0])
    sections.extend([
        "",
        "BUILD RADAR",
        f"Idea to validate: {idea_name}",
        idea_desc,
        "Before building: check existing alternatives and confirm that users actually have this problem.",
        "",
        "CONTENT CHECKLIST",
        "1. Open the primary source and verify the claim.",
        "2. Find the overlooked technical or practical detail.",
        "3. Write one clear position supported by evidence.",
        "4. Keep speculation labeled and approve the final post manually.",
    ])
    digest = "\n".join(sections)
    if len(digest) > 3900:
        digest = digest[:3870].rsplit("\n", 1)[0] + "\n[Digest shortened; open the source links above.]"
    return digest
