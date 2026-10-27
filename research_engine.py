"""Deterministic candidate triage for the crypto research pipeline.

This module only prioritizes research candidates. It is not a truth detector and
never substitutes for source verification or the editorial model's publication gate.
"""
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
import re


CONTENT_PATTERNS = (
    ("investigation", re.compile(r"\b(exploit|hack|drain|stolen|vulnerability|postmortem|suspicious|wallet flow|incident|attack)\b", re.I)),
    ("education", re.compile(r"\b(how to|guide|tutorial|explained|what is|learn|step by step)\b", re.I)),
    ("analysis", re.compile(r"\b(tokenomics|token burn|burns|unlock|emissions|revenue|fees|tvl|liquidity|supply|wallet growth|market structure|governance)\b", re.I)),
    ("tool_discovery", re.compile(r"\b(open source|developer tool|sdk|api|github|library|dashboard|release notes)\b", re.I)),
    ("breaking_news", re.compile(r"\b(launch|launched|announces|announced|upgrade|released|release|proposal|approved|integrates|integration|mainnet|testnet)\b", re.I)),
)

SPECIFICITY_PATTERNS = (
    re.compile(r"\b\d+(?:\.\d+)?\s?(?:%|million|billion|thousand|usd|eth|btc|usdc)\b", re.I),
    re.compile(r"\b0x[a-f0-9]{8,}\b", re.I),
    re.compile(r"\b(transaction hash|tx hash|contract address|block height|pull request|postmortem|collateral factor|liquidation threshold)\b", re.I),
)

GENERIC_PHRASES = (
    "could shape crypto", "worth tracking", "huge news", "game changer",
    "this is bullish", "mass adoption is coming", "what happens next",
    "crypto is changing", "the future of crypto",
)


def classify_content(item):
    """Return an editorial lane based on the item and its existing source lane."""
    lane = str(item.get("content_lane") or "").lower()
    if lane == "research_guides":
        return "education"
    if lane == "skill_showcase":
        return "practical_framework"
    text = str(item.get("text") or "")
    for name, pattern in CONTENT_PATTERNS:
        if pattern.search(text):
            return name
    return "general_finding"


def score_candidate(item, now=None):
    """Return a transparent 0-100 triage score and its dimension breakdown.

    Scores are heuristics for ordering research work, not truth/confidence scores.
    The downstream source and editorial checks remain mandatory.
    """
    now = now or datetime.now(timezone.utc)
    text = " ".join(str(item.get("text") or "").split())
    lower = text.lower()
    source = str(item.get("source") or "").lower()
    url = str(item.get("url") or "")
    host = (urlparse(url).hostname or "").lower()
    lane = str(item.get("content_lane") or "").lower()

    significance = 2.0
    if re.search(r"\b(exploit|hack|stolen|security incident|stablecoin|payments|governance|mainnet|upgrade|revenue|fees)\b", lower):
        significance += 1.5
    if re.search(r"\b(million|billion|\d+(?:\.\d+)?%|0x[a-f0-9]{8,})\b", lower):
        significance += 1.0
    significance = min(5.0, significance)

    evidence = 1.5
    if source in {"web", "howto_research", "skill_research", "medium"}:
        evidence += 1.0
    if host.endswith(".gov") or host.endswith(".edu") or host.startswith("docs.") or "github.com/" in url.lower():
        evidence += 1.0
    if any(pattern.search(text) for pattern in SPECIFICITY_PATTERNS):
        evidence += 1.5
    elif len(text) > 180:
        evidence += 0.5
    evidence = min(5.0, evidence)

    information = 1.5
    if len(text) >= 100:
        information += 1.0
    if len(text) >= 220:
        information += 0.75
    if any(pattern.search(text) for pattern in SPECIFICITY_PATTERNS):
        information += 1.0
    if any(phrase in lower for phrase in GENERIC_PHRASES):
        information -= 1.5
    information = max(0.0, min(5.0, information))

    timeliness = 2.5
    raw_date = item.get("created_at")
    try:
        if isinstance(raw_date, (int, float)) or str(raw_date).strip().isdigit():
            stamp = float(raw_date)
            if stamp > 100000000000:
                stamp /= 1000
            created = datetime.fromtimestamp(stamp, timezone.utc)
        else:
            created = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00"))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            else:
                created = created.astimezone(timezone.utc)
        age = now - created
        if age <= timedelta(hours=24):
            timeliness = 5.0
        elif age <= timedelta(days=3):
            timeliness = 4.0
        elif age <= timedelta(days=7):
            timeliness = 3.0
        elif age <= timedelta(days=30) and lane == "research_guides":
            timeliness = 4.0
        elif age > timedelta(days=30):
            timeliness = 1.0
    except (TypeError, ValueError, OverflowError, OSError):
        # Unknown timestamps should not be treated as fresh.
        timeliness = 2.0

    educational = 4.5 if lane == "research_guides" else 3.5 if re.search(r"\b(explains|explained|how to|guide|mechanism|why)\b", lower) else 2.0
    originality = 3.0
    if re.search(r"\b(compared with|unlike|instead of|before and after|because|mechanism|trade-off|tradeoff)\b", lower):
        originality += 1.0
    if any(phrase in lower for phrase in GENERIC_PHRASES):
        originality -= 1.0
    originality = max(0.0, min(5.0, originality))

    dimensions = {
        "significance": round(significance, 2),
        "evidence_quality": round(evidence, 2),
        "information_value": round(information, 2),
        "timeliness": round(timeliness, 2),
        "educational_value": round(educational, 2),
        "originality": round(originality, 2),
    }
    weights = {
        "significance": 0.25,
        "evidence_quality": 0.25,
        "information_value": 0.20,
        "timeliness": 0.10,
        "educational_value": 0.10,
        "originality": 0.10,
    }
    score = round(sum(dimensions[key] / 5 * weight * 100 for key, weight in weights.items()))
    return {
        "content_type": classify_content(item),
        "score": score,
        "dimensions": dimensions,
    }


def annotate_candidate(item, now=None):
    """Attach triage metadata without mutating the source evidence."""
    result = dict(item)
    ranking = score_candidate(result, now=now)
    result["_research_type"] = ranking["content_type"]
    result["_priority_score"] = ranking["score"]
    result["_priority_dimensions"] = ranking["dimensions"]
    return result
