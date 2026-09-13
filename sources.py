from __future__ import annotations

from models import SourceAccount


# Free, public crypto-news and community feeds. The feed itself is not treated
# as proof of relevance; the crypto-relevance filter decides what reaches the feed.
SOURCE_ACCOUNTS = [
    SourceAccount("coindesk", "CoinDesk", "crypto_news", 94, 94),
    SourceAccount("cointelegraph", "Cointelegraph", "crypto_news", 90, 90),
    SourceAccount("decrypt", "Decrypt", "crypto_news", 88, 90),
    SourceAccount("cryptoslate", "CryptoSlate", "crypto_news", 84, 86),
    SourceAccount("bitcoinmagazine", "Bitcoin Magazine", "bitcoin_news", 88, 88),
    SourceAccount("thedefiant", "The Defiant", "defi_news", 86, 88),

    # Public Reddit community feeds: useful for early narratives, sentiment,
    # project chatter, launches, controversies and ecosystem discussion.
    SourceAccount("reddit_cryptocurrency", "Reddit r/CryptoCurrency", "crypto_community", 82, 82),
    SourceAccount("reddit_bitcoin", "Reddit r/Bitcoin", "bitcoin_community", 80, 80),
    SourceAccount("reddit_ethereum", "Reddit r/ethereum", "ethereum_community", 80, 80),
    SourceAccount("reddit_solana", "Reddit r/solana", "solana_community", 80, 80),
    SourceAccount("reddit_defi", "Reddit r/DeFi", "defi_community", 78, 80),
    SourceAccount("reddit_ethfinance", "Reddit r/ethfinance", "ethereum_community", 78, 80),
    SourceAccount("reddit_ethtrader", "Reddit r/ethtrader", "ethereum_community", 76, 76),
    SourceAccount("reddit_cryptomarkets", "Reddit r/CryptoMarkets", "market_community", 76, 78),

    # Protocol-native feeds: direct ecosystem announcements and developments.
    SourceAccount("ethereum_blog", "Ethereum Foundation Blog", "ethereum_news", 92, 92),
    SourceAccount("solana_news", "Solana News", "solana_news", 92, 92),
    SourceAccount("uniswap_blog", "Uniswap Labs Blog", "defi_news", 88, 88),
]


def enabled_sources() -> list[SourceAccount]:
    return [source for source in SOURCE_ACCOUNTS if source.enabled]
