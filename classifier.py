import re

CAMPAIGN_TYPES = {
    "airdrop": ["airdrop", "air drop"],
    "points": ["points", "point campaign", "points program"],
    "creator": ["creator", "content creator", "content campaign"],
    "video": ["video contest", "video competition", "make a video"],
    "meme": ["meme contest", "meme competition", "meme campaign"],
    "art": ["art contest", "art competition", "artist"],
    "quest": ["quest", "tasks", "missions", "campaign"],
    "ambassador": ["ambassador", "ambassadors"],
    "hackathon": ["hackathon", "builders", "buildathon"],
    "testnet": ["testnet", "devnet", "mainnet"],
    "ido": ["ido", "token sale", "public sale"],
    "nft": ["nft", "mint", "allowlist", "whitelist"],
    "grant": ["grant", "grants", "funding", "bounty"],
    "trend": ["trending", "narrative", "viral", "meta"],
}
ACTION_WORDS = ["join", "apply", "register", "submit", "earn", "reward", "win", "deadline", "ends", "open", "ongoing", "season", "round", "wave"]

def classify(item):
    low = item.get("text", "").lower()
    types = [label for label, words in CAMPAIGN_TYPES.items() if any(w in low for w in words)]
    action_hits = sum(bool(re.search(r"\b" + re.escape(w) + r"\b", low)) for w in ACTION_WORDS)
    item["types"] = types or ["trend"]
    item["campaign_score"] = min(100, len(types) * 12 + action_hits * 8 + (10 if item.get("source") == "x" else 0))
    return item

def is_relevant(item):
    return item.get("campaign_score", 0) >= 20
