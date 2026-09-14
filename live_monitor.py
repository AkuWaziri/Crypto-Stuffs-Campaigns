from evm_monitor import parse_swap_transfer
from live_config import EVM_CHAIN, EVM_WALLETS, POLL_LIMIT, SOLANA_WALLETS
from solana_monitor import monitor_wallet


def collect_solana() -> list:
    events = []
    for wallet in SOLANA_WALLETS:
        events.extend(monitor_wallet(wallet, limit=POLL_LIMIT))
    return events


def collect_evm() -> list:
    """Consume normalized EVM swap records supplied by a future provider adapter.

    Raw EVM RPC logs are intentionally not treated as buys/sells because a token
    transfer alone does not prove a trade. The provider adapter must supply
    receivedTarget/spentTarget and then this module passes it to the existing
    EVM classifier.
    """
    return []


def collect_live_events() -> list:
    return collect_solana() + collect_evm()
