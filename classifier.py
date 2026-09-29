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
        "launched", "prototype", "mvp", "alpha", "beta", "demo", "maker",
        "builder", "builders",
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
        "gaming", "social", "identity", "ticketing", "real world",
    ),
    # Campaign/opportunity types. These are first-class feed items, not
    # dependent on also matching building/research/humor categories.
    "hackathon": (
        "hackathon", "hackathons", "buildathon", "builder competition",
        "hackathon track", "hackathon prize", "hackathon bounty",
    ),
    "video": (
        "video contest", "video competition", "video challenge", "video campaign",
        "make a video", "create a video", "video creator", "youtube contest",
        "shorts contest", "reels contest", "tiktok contest",
    ),
    "art_design": (
        "art contest", "art competition", "design contest", "design competition",
        "design challenge", "creative contest", "illustration contest",
        "poster contest", "ui/ux contest", "ui ux contest",
    ),
    "content": (
        "content contest", "content competition", "content campaign",
        "creator campaign", "creator contest", "writing contest", "writing competition",
        "article contest", "thread contest", "content challenge",
    ),
    "meme": (
        "meme contest", "meme competition", "meme challenge", "meme campaign",
        "meme bounty",
    ),
    "bounty": (
        "bounty", "bounties", "bug bounty", "build bounty", "developer bounty",
        "content bounty", "creative bounty", "community bounty",
    ),
    "grant": (
        "grant", "grants", "grant program", "builder grant", "creator grant",
        "community grant", "funding opportunity",
    ),
    "ambassador": (
        "ambassador program", "ambassador campaign", "community ambassador",
        "creator program", "advocate program",
    ),
    "quest": (
        "quest", "quests", "galxe", "zealy", "task campaign", "missions",
    ),
    "airdrop": (
        "airdrop", "airdrop campaign", "token rewards", "token reward",
        "points program", "points campaign",
    ),
    "testnet": (
        "testnet campaign", "testnet rewards", "testnet incentive", "devnet rewards",
        "testnet bounty", "testnet program",
    ),
    "trading": (
        "trading competition", "trading contest", "trading challenge",
        "trading campaign", "volume competition", "pnl competition",
    ),
    "nft_token": (
        "nft contest", "nft campaign", "nft rewards", "mint campaign",
        "token sale", "token launch campaign", "ido", "ico",
    ),
    "research_campaign": (
        "research contest", "research competition", "research bounty",
        "research campaign", "research challenge",
    ),
    "innovation": (
        "idea contest", "idea competition", "innovation contest",
        "innovation challenge", "startup competition", "pitch competition",
        "product challenge",
    ),
    "community": (
        "community campaign", "community challenge", "community contest",
        "community rewards", "community program",
    ),
    "reward": (
        "reward", "rewards", "prize", "prizes", "cash prize", "crypto prize",
        "earn crypto", "earn tokens", "paid campaign", "paid opportunity",
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
    # requested form such as a campaign/opportunity, building, research, or humor.
    if item.get("source") in {"x", "reddit", "medium", "telegram", "bluesky", "mastodon"}:
        crypto = crypto or bool(item.get("crypto_query"))

    item["types"] = types
    item["crypto_relevant"] = crypto
    item["content_relevant"] = bool(types)
    return item

def is_relevant(item):
    return bool(item.get("crypto_relevant") and item.get("content_relevant"))
