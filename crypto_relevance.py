from __future__ import annotations

import re


CRYPTO_TERMS = {
    "crypto", "cryptocurrency", "bitcoin", "btc", "ethereum", "eth", "solana", "sol",
    "blockchain", "web3", "defi", "dex", "cex", "stablecoin", "stablecoins", "token",
    "tokens", "tokenized", "tokenization", "memecoin", "memecoin", "meme coin", "airdrop",
    "airdrops", "staking", "yield", "lending", "liquidity", "onchain", "on-chain", "wallet",
    "smart contract", "dao", "nft", "nfts", "layer 1", "layer 2", "l2", "rollup", "bridge",
    "protocol", "mainnet", "testnet", "gas", "validator", "solana", "base", "arbitrum",
    "optimism", "avalanche", "sui", "xrp", "defi", "payments", "crypto payments",
    "stablecoins", "usdc", "usdt", "ai agent", "ai agents", "crypto agent", "crypto agents",
}


def _terms(text: str) -> set[str]:
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return {term for term in CRYPTO_TERMS if term in normalized}


def is_crypto_relevant(title: str, text: str) -> bool:
    """Return True when the actual story is materially crypto/Web3 related."""
    return bool(_terms(f"{title} {text}"))
