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

# The only active content category.
FUNNY_CREATIVE_TERMS = (
    "satire", "satirical", "parody", "parodic", "spoof", "irony", "ironic",
    "ironic crypto", "ironic web3", "joke", "jokes", "comedy", "funny",
    "hilarious", "humor", "humorous", "meme", "memes", "comic", "comics",
    "cartoon", "shitpost", "shitposts", "shitposting", "shitposter",
    "crypto be like", "web3 be like", "crypto irl", "crypto in real life",
    "crypto moment", "crypto moments", "crypto situation", "crypto situations",
    "funny crypto take", "funny crypto scene", "crypto humor", "web3 humor",
)

def _has_term(text, terms):
    return any(
        re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text)
        for term in terms
    )

def classify(item):
    text = " ".join(str(item.get("text", "")).split())
    low = text.lower()
    crypto = _has_term(low, CRYPTO_TERMS)
    funny = _has_term(low, FUNNY_CREATIVE_TERMS)

    if item.get("source") in {"x", "reddit", "medium", "telegram", "bluesky", "farcaster", "mastodon"}:
        crypto = crypto or bool(item.get("crypto_query"))

    item["types"] = ["funny_creative_crypto"] if funny else []
    item["crypto_relevant"] = crypto
    item["content_relevant"] = funny
    return item

def is_relevant(item):
    return bool(item.get("crypto_relevant") and item.get("content_relevant"))
