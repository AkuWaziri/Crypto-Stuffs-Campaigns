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

# ONLY crypto humor/culture categories requested by the user.
CONTENT_TYPES = {
    "crypto_satire": (
        "crypto satire", "crypto satirical", "web3 satire", "web3 satirical",
        "crypto parody", "web3 parody", "crypto spoof",
    ),
    "funny_crypto_take": (
        "funny crypto take", "funny crypto", "funny web3", "hilarious crypto",
        "hilarious web3", "crypto joke", "crypto jokes", "crypto comedy",
        "crypto funny", "crypto lol", "crypto lmao",
    ),
    "meme_comic_crypto": (
        "crypto meme", "crypto memes", "web3 meme", "web3 memes",
        "crypto comic", "crypto comics", "web3 comic", "web3 comics",
        "crypto cartoon", "web3 cartoon",
    ),
    "funny_crypto_scene": (
        "funny crypto scene", "crypto scene", "crypto moment", "crypto moments",
        "crypto situation", "crypto situations", "crypto be like",
        "web3 be like", "crypto irl", "crypto in real life",
    ),
    "crypto_shitpost": (
        "crypto shitpost", "crypto shitposts", "crypto shitposting",
        "web3 shitpost", "web3 shitposts", "web3 shitposting",
        "crypto shit poster", "crypto shitposter",
    ),
    "crypto_metaphor": (
        "crypto metaphor", "crypto metaphors", "web3 metaphor", "web3 metaphors",
        "crypto analogy", "crypto analogies", "web3 analogy", "web3 analogies",
        "crypto is like", "crypto feels like", "crypto basically",
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
