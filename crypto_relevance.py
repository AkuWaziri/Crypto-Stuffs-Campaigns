from __future__ import annotations

import re


STRONG_CRYPTO_TERMS = {
    "crypto", "cryptocurrency", "bitcoin", "btc", "ethereum", "eth", "solana",
    "blockchain", "web3", "defi", "dex", "cex", "stablecoin", "stablecoins", "token",
    "tokens", "tokenized", "tokenization", "memecoin", "meme coin", "airdrop", "airdrops",
    "staking", "yield", "lending", "liquidity", "onchain", "on-chain", "wallet", "wallets",
    "smart contract", "dao", "nft", "nfts", "layer 1", "layer 2", "l2", "rollup", "bridge",
    "mainnet", "testnet", "validator", "arbitrum", "optimism", "avalanche", "sui", "xrp",
    "usdc", "usdt", "crypto payments", "ai agent", "ai agents", "crypto agent", "crypto agents",
}


def _normalized(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _contains_term(text: str, term: str) -> bool:
    pattern = rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _matched_terms(text: str) -> set[str]:
    return {
        term
        for term in STRONG_CRYPTO_TERMS
        if _contains_term(text, term)
    }


def is_crypto_relevant(title: str, text: str) -> bool:
    """Return True when the actual story is materially crypto/Web3 related."""
    return bool(_matched_terms(_normalized(f"{title} {text}")))
