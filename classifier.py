import re

# Broad crypto relevance: the bot is not limited to a fixed list of content formats.
# Any clearly crypto-related post can pass, whether it is news, research, a launch,
# a market move, a product, an opinion, a campaign, a meme, or something unexpected.
CRYPTO_TERMS = (
    "crypto", "cryptocurrency", "bitcoin", "btc", "ethereum", "eth", "solana",
    "sol", "defi", "web3", "blockchain", "onchain", "on-chain", "dao", "nft",
    "stablecoin", "token", "tokens", "altcoin", "memecoin", "wallet", "layer 2",
    "l2", "rollup", "protocol", "dapp", "staking", "yield", "liquidity", "dex",
    "cex", "evm", "zk", "restaking", "smart contract", "smart contracts",
    "account abstraction", "depin", "layerzero", "arbitrum", "optimism",
    "base", "cosmos", "polkadot", "avalanche", "near", "sui", "aptos",
    "token unlock", "token launch", "tokenomics", "governance proposal",
    "validator", "validators", "bridge", "bridging", "gas fees", "gas fee",
    "transaction hash", "tx hash", "liquidation", "liquidations", "tvl",
    "total value locked", "funding round", "mainnet", "testnet", "whitepaper",
    "seed phrase", "private key", "crypto exchange", "exchange listing",
    "onchain data", "on-chain data", "wallet address", "block explorer",
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
SECURITY_TERMS = ("security", "exploit", "exploits", "hacked", "hack", "vulnerability", "vulnerabilities", "suspicious wallet", "wallet movements", "drained", "drainer", "phishing", "rug pull")


def _has_term(text, terms):
    return any(
        re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text)
        for term in terms
    )


def classify(item):
    text = " ".join(str(item.get("text", "")).split())
    low = text.lower()
    source = str(item.get("source", "")).lower()
    known_sources = {"x", "reddit", "medium", "telegram", "bluesky", "farcaster", "mastodon"}
    crypto_query_match = source in known_sources and bool(item.get("crypto_query"))
    crypto = _has_term(low, CRYPTO_TERMS) or crypto_query_match

    types = []
    if _has_term(low, SATIRE_TERMS):
        types.extend(["satire", "funny_creative_crypto"])
    if _has_term(low, RESEARCH_TERMS):
        types.append("research")
        if _has_term(low, ("finding", "findings")):
            types.append("finding")
    if _has_term(low, AIRDROP_TERMS):
        types.append("airdrop")
    if _has_term(low, HACKATHON_TERMS):
        types.append("hackathon")
    if _has_term(low, REWARD_TERMS):
        types.append("reward")
    if _has_term(low, VIDEO_TERMS):
        types.append("video")
    if _has_term(low, SECURITY_TERMS):
        types.append("security")
    if crypto and not types:
        types.append("crypto_general")

    item["types"] = list(dict.fromkeys(types))
    item["crypto_relevant"] = crypto
    # Broad inclusion: any crypto-related item qualifies, even when it does not
    # match a predefined campaign, research, satire, or security category.
    item["content_relevant"] = crypto or bool(types)
    return item


def is_relevant(item):
    return bool(item.get("crypto_relevant") and item.get("content_relevant"))
