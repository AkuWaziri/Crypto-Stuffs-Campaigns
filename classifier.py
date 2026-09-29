import re

CRYPTO_TERMS = (
    "crypto", "cryptocurrency", "bitcoin", "btc", "ethereum", "eth", "solana",
    "sol", "defi", "web3", "blockchain", "onchain", "on-chain", "dao", "nft",
    "stablecoin", "token", "tokens", "altcoin", "memecoin", "wallet", "layer 2",
    "l2", "rollup", "protocol", "dapp", "staking", "yield", "liquidity", "dex",
    "cex", "evm", "zk", "restaking", "smart contract", "smart contracts",
    "account abstraction", "depin", "layerzero", "arbitrum", "optimism",
    "base", "cosmos", "polkadot", "avalanche", "near", "sui", "aptos",
)

# Deliberately narrow taxonomy: only research/discovery/analysis,
# crypto-native humor/culture, and hacks/security. Similar forms are
# included where they are natural variants of the requested categories.
CONTENT_TYPES = {
    "research": (
        "research", "study", "paper", "data", "report", "findings",
        "experiment", "investigation", "deep dive", "deep-dive",
        "case study", "postmortem", "forensics", "breakdown",
    ),
    "onchain_findings": (
        "on-chain findings", "onchain findings", "on-chain data",
        "onchain data", "on-chain analysis", "onchain analysis",
        "on-chain activity", "onchain activity", "wallet activity",
        "address activity", "transaction analysis",
    ),
    "analysis": (
        "analysis", "analyze", "analysing", "analyzing", "breakdown",
        "thesis", "market structure", "protocol analysis", "data analysis",
    ),
    "discovery": (
        "discovery", "discovered", "discover", "reveals", "revealed",
        "finding", "findings", "interesting", "unexpected", "surprising",
        "observation", "observed", "odd", "weird", "hidden", "overlooked",
        "under the radar", "noticed", "new insight",
    ),
    "satire": (
        "satire", "satirical", "parody", "parodying", "mocking", "mock",
    ),
    "irony": (
        "ironic", "irony", "ironically", "plot twist", "the irony",
    ),
    "funny": (
        "funny", "hilarious", "lol", "lmao", "haha", "joke", "jokes",
        "laugh", "laughing", "comedy",
    ),
    "metaphor": (
        "metaphor", "metaphorical", "analogy", "analogous", "like a",
        "is basically", "think of it as",
    ),
    "comic": (
        "comic", "comics", "cartoon", "illustration", "illustrated",
    ),
    "meme": (
        "meme", "memes", "memeing", "shitpost", "shitposting",
    ),
    "hack_security": (
        "hack", "hacked", "hacking", "exploit", "exploited", "exploit",
        "vulnerability", "vulnerable", "security", "security incident",
        "breach", "attack", "attacked", "drained", "drainer",
        "smart contract exploit", "protocol exploit", "defi exploit",
        "postmortem", "root cause", "incident response",
    ),
}

def _has_term(text, terms):
    return any(
        re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text)
        for term in terms
    )

def classify(item):
    text = " ".join(str(item.get("text", "")).split())
    low = text.lower()
    crypto = _has_term(low, CRYPTO_TERMS)
    types = [label for label, words in CONTENT_TYPES.items() if _has_term(low, words)]

    if item.get("source") in {"x", "reddit", "medium", "telegram", "bluesky", "mastodon"}:
        crypto = crypto or bool(item.get("crypto_query"))

    item["types"] = types
    item["crypto_relevant"] = crypto
    item["content_relevant"] = bool(types)
    return item

def is_relevant(item):
    return bool(item.get("crypto_relevant") and item.get("content_relevant"))
