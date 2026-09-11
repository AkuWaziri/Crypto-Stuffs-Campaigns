from __future__ import annotations

from models import SourceAccount


# Free, public crypto-news feeds. The registry describes source quality;
# qualification is still decided by the trend-scoring layer.
SOURCE_ACCOUNTS = [
    SourceAccount("coindesk", "CoinDesk", "crypto_news", 94, 94),
    SourceAccount("cointelegraph", "Cointelegraph", "crypto_news", 90, 90),
    SourceAccount("decrypt", "Decrypt", "crypto_news", 88, 90),
    SourceAccount("cryptoslate", "CryptoSlate", "crypto_news", 84, 86),
    SourceAccount("bitcoinmagazine", "Bitcoin Magazine", "bitcoin_news", 88, 88),
    SourceAccount("thedefiant", "The Defiant", "defi_news", 86, 88),
]


def enabled_sources() -> list[SourceAccount]:
    return [source for source in SOURCE_ACCOUNTS if source.enabled]
