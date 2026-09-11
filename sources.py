from __future__ import annotations

from models import SourceAccount


# Initial high-signal registry. This is data, not a guarantee that an account
# produces launch-worthy narratives. The scoring layer decides that separately.
SOURCE_ACCOUNTS = [
    SourceAccount("elonmusk", "Elon Musk", "macro", 98, 85),
    SourceAccount("saylor", "Michael Saylor", "bitcoin", 96, 90),
    SourceAccount("VitalikButerin", "Vitalik Buterin", "ethereum", 98, 95),
    SourceAccount("CathieDWood", "Cathie Wood", "macro", 90, 82),
    SourceAccount("brian_armstrong", "Brian Armstrong", "exchange", 93, 91),
    SourceAccount("balajis", "Balaji Srinivasan", "macro_crypto", 94, 84),
    SourceAccount("cdixon", "Chris Dixon", "web3", 88, 91),
    SourceAccount("lookonchain", "Lookonchain", "onchain_intelligence", 94, 90),
]


def enabled_sources() -> list[SourceAccount]:
    return [source for source in SOURCE_ACCOUNTS if source.enabled]
