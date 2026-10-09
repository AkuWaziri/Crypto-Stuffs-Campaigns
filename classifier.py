import re

CRYPTO_TERMS = (
    "crypto", "cryptocurrency", "bitcoin", "btc", "ethereum", "eth", "solana", "sol",
    "defi", "web3", "blockchain", "onchain", "on-chain", "dao", "nft", "stablecoin",
    "token", "tokens", "altcoin", "memecoin", "wallet", "layer 2", "l2", "rollup",
    "protocol", "dapp", "staking", "yield", "liquidity", "dex", "cex", "evm", "zk",
    "restaking", "smart contract", "smart contracts", "account abstraction", "depin",
    "layerzero", "arbitrum", "optimism", "base", "cosmos", "polkadot", "avalanche",
    "near", "sui", "aptos", "airdrop", "onchain", "stablecoins",
)

CATEGORY_TERMS = {
    "security": ("exploit", "hack", "hacked", "security", "vulnerability", "rug pull", "phishing"),
    "research": ("research", "finding", "investigation", "analysis", "traced", "onchain"),
    "airdrop": ("airdrop", "airdrop campaign", "claim"),
    "hackathon": ("hackathon",),
    "reward": ("reward", "rewards", "prize", "prizes", "incentive", "points"),
    "video": ("video", "short explainer", "clip"),
    "build": ("build", "builder", "builders", "developer", "tool", "open source", "release"),
    "payments": ("payment", "payments", "stablecoin", "stablecoins"),
    "adoption": ("adoption", "users", "integrated", "integration", "launched"),
    "governance": ("governance", "proposal", "vote", "compensation", "refund"),
    "market": ("price", "trading", "volume", "market", "memecoin"),
}


def _has_term(text, terms):
    return any(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text) for term in terms)


def classify(item):
    text = " ".join(str(item.get("text", "")).split())
    low = text.lower()
    crypto = _has_term(low, CRYPTO_TERMS)
    if item.get("source") in {"x", "reddit", "medium", "telegram", "bluesky", "farcaster", "mastodon"}:
        crypto = crypto or bool(item.get("crypto_query"))
    types = [name for name, terms in CATEGORY_TERMS.items() if _has_term(low, terms)]
    if crypto and any(term in low for term in ("research", "finding", "investigation", "trace", "traced", "analysis")):
        if "finding" not in types:
            types.append("finding")
    item["types"] = types or (["crypto"] if crypto else [])
    item["crypto_relevant"] = crypto
    item["content_relevant"] = bool(crypto and text)
    return item


def is_relevant(item):
    return bool(item.get("crypto_relevant") and item.get("content_relevant"))
