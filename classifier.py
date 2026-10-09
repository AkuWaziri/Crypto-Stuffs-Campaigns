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

SATIRE_TERMS = (
    "satire", "satirical", "parody", "parodic", "spoof", "irony", "ironic",
    "joke", "jokes", "comedy", "funny", "hilarious", "humor", "humorous",
    "meme", "memes", "comic", "comics", "cartoon", "shitpost", "shitposts",
    "shitposting", "shitposter", "crypto be like", "web3 be like", "crypto irl",
    "crypto in real life", "crypto moment", "crypto moments", "crypto humor",
    "web3 humor",
)
RESEARCH_TERMS = ("research", "study", "investigation", "analysis", "report", "findings", "finding")
AIRDROP_TERMS = ("airdrop", "airdrops", "air drop", "token campaign", "crypto campaign", "incentive campaign")
HACKATHON_TERMS = ("hackathon", "hackathons")
REWARD_TERMS = ("reward", "rewards", "prize", "prizes", "bounty", "bounties", "grant", "grants")
VIDEO_TERMS = ("video", "videos", "video challenge", "video campaign", "short explainer")


def _has_term(text, terms):
    return any(
        re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text)
        for term in terms
    )


def classify(item):
    text = " ".join(str(item.get("text", "")).split())
    low = text.lower()
    crypto = _has_term(low, CRYPTO_TERMS)
    source = str(item.get("source", "")).lower()
    if source in {"x", "reddit", "medium", "telegram", "bluesky", "farcaster", "mastodon"}:
        crypto = crypto or bool(item.get("crypto_query"))

    types = []
    satire = _has_term(low, SATIRE_TERMS)
    research = _has_term(low, RESEARCH_TERMS)
    airdrop = _has_term(low, AIRDROP_TERMS)
    hackathon = _has_term(low, HACKATHON_TERMS)
    reward = _has_term(low, REWARD_TERMS)
    video = _has_term(low, VIDEO_TERMS)

    if satire:
        types.extend(["satire", "funny_creative_crypto"])
    if research:
        types.append("research")
        if _has_term(low, ("finding", "findings")):
            types.append("finding")
    if airdrop:
        types.append("airdrop")
    if hackathon:
        types.append("hackathon")
    if reward:
        types.append("reward")
    if video:
        types.append("video")

    item["types"] = list(dict.fromkeys(types))
    item["crypto_relevant"] = crypto
    item["content_relevant"] = bool(types)
    return item


def is_relevant(item):
    return bool(item.get("crypto_relevant") and item.get("content_relevant"))
