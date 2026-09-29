import re

CRYPTO_TERMS = (
    "crypto", "cryptocurrency", "bitcoin", "btc", "ethereum", "eth", "solana",
    "sol", "defi", "web3", "blockchain", "onchain", "on-chain", "dao", "nft",
    "stablecoin", "token", "tokens", "altcoin", "memecoin", "wallet", "layer 2",
    "l2", "rollup", "protocol", "dapp", "staking", "yield", "liquidity", "dex",
    "cex", "evm", "zk", "restaking", "smart contract", "smart contracts",
    "account abstraction", "depIN", "depin", "layerzero", "arbitrum", "optimism",
    "base", "cosmos", "polkadot", "avalanche", "near", "sui", "aptos",
)

CONTENT_TYPES = {
    "satire": ("satire", "satirical", "parody", "parodying", "mocking", "mock"),
    "ironic": ("ironic", "irony", "ironically", "plot twist"),
    "funny": ("funny", "hilarious", "lol", "lmao", "haha", "joke", "jokes", "laugh"),
    "metaphor": ("metaphor", "metaphorical", "analogy", "analogous", "like a", "is basically"),
    "research": (
        "research", "study", "paper", "data", "analysis", "report", "findings",
        "experiment", "investigation", "breakdown", "on-chain analysis",
    ),
    "comic": ("comic", "comics", "cartoon", "illustration", "illustrated", "meme"),
    "finding": (
        "finding", "findings", "discovered", "discovery", "reveals", "revealed",
        "interesting", "unexpected", "observation", "odd", "weird",
    ),
    "building": (
        "building", "build", "built", "shipping", "shipped", "ship", "launching",
        "launched", "prototype", "prototype", "mvp", "alpha", "beta", "demo",
        "hackathon", "maker", "builder", "builders",
    ),
    "idea": (
        "idea", "ideas", "concept", "what if", "imagine", "someone should build",
        "should build", "could build", "would be cool", "i wish there was",
        "new way", "new primitive", "unmet need",
    ),
    "product": (
        "product", "app", "application", "tool", "dapp", "platform", "service",
        "consumer", "user experience", "ux", "onboarding", "payments",
    ),
    "technical": (
        "technical", "implementation", "architecture", "infrastructure", "infra",
        "protocol design", "mechanism", "primitive", "smart contract", "sdk",
        "api", "library", "developer", "developers", "devtool", "devtools",
    ),
    "opensource": (
        "open source", "opensource", "github", "repo", "repository", "sdk",
        "library", "framework", "code", "pull request",
    ),
    "experiment": (
        "experiment", "experimental", "prototype", "proof of concept", "poc",
        "testnet", "testing", "trying", "tested", "benchmark",
    ),
    "integration": (
        "integration", "integrate", "integrated", "connect", "connected",
        "crypto +", "web3 +", "with ai", "with gaming", "with payments",
        "with social", "with depin",
    ),
    "problem": (
        "problem", "pain point", "bottleneck", "friction", "challenge",
        "hard to", "broken", "missing", "gap", "need a better",
    ),
    "application": (
        "use case", "use cases", "payments", "remittance", "commerce", "creator",
        "gaming", "social", "identity", "ticketing", "commerce", "real world",
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

    # Source queries can establish crypto context; content still needs a
    # requested form such as building, ideas, research, technical, or humor.
    if item.get("source") in {"x", "reddit", "medium", "telegram", "bluesky", "mastodon"}:
        crypto = crypto or bool(item.get("crypto_query"))

    item["types"] = types
    item["crypto_relevant"] = crypto
    item["content_relevant"] = bool(types)
    return item

def is_relevant(item):
    return bool(item.get("crypto_relevant") and item.get("content_relevant"))
