import re

CRYPTO_TERMS = (
    "crypto", "cryptocurrency", "bitcoin", "btc", "ethereum", "eth", "solana",
    "sol", "defi", "web3", "blockchain", "onchain", "on-chain", "dao", "nft",
    "stablecoin", "token", "tokens", "altcoin", "memecoin", "memecoin", "airdrop",
    "wallet", "layer 2", "l2", "rollup", "protocol", "dapp", "staking",
    "yield", "liquidity", "dex", "cex", "evm", "zk", "restaking",
)

CONTENT_TYPES = {
    "satire": ("satire", "satirical", "parody", "parodying", "mocking", "mock"),
    "ironic": ("ironic", "irony", "ironically", "ironic that", "plot twist"),
    "funny": ("funny", "hilarious", "lol", "lmao", "haha", "joke", "jokes", "laugh"),
    "metaphor": ("metaphor", "metaphorical", "analogy", "like a", "is basically"),
    "research": ("research", "study", "paper", "data", "analysis", "report", "findings", "experiment", "investigation"),
    "comic": ("comic", "comics", "cartoon", "illustration", "illustrated", "meme"),
    "finding": ("finding", "findings", "discovered", "discovery", "reveals", "revealed", "interesting", "unexpected", "observation"),
}

def _has_term(text, terms):
    return any(re.search(r"(?<!\\w)" + re.escape(term) + r"(?!\\w)", text) for term in terms)

def classify(item):
    text = " ".join(str(item.get("text", "")).split())
    low = text.lower()

    crypto = _has_term(low, CRYPTO_TERMS)
    types = [label for label, words in CONTENT_TYPES.items() if _has_term(low, words)]

    # The source query itself can establish crypto context, but the final item
    # must still match one of the requested content forms.
    if item.get("source") in {"x", "reddit", "medium", "telegram", "bluesky", "mastodon"}:
        crypto = crypto or bool(item.get("crypto_query"))

    item["types"] = types
    item["crypto_relevant"] = crypto
    item["content_relevant"] = bool(types)
    return item

def is_relevant(item):
    return bool(item.get("crypto_relevant") and item.get("content_relevant"))
