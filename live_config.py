import os


def env_list(name: str) -> list[str]:
    raw = os.getenv(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


SOLANA_WALLETS = env_list("SOLANA_WALLETS")
EVM_WALLETS = env_list("EVM_WALLETS")
EVM_CHAIN = os.getenv("EVM_CHAIN", "ethereum")
POLL_LIMIT = max(1, min(int(os.getenv("POLL_LIMIT", "20")), 100))
LIVE_MIN_USD = max(1.0, float(os.getenv("LIVE_MIN_USD", "100000")))
LIVE_WINDOW_MINUTES = max(1, min(int(os.getenv("LIVE_WINDOW_MINUTES", "6")), 30))
LIVE_MAX_EVENTS = max(1, min(int(os.getenv("LIVE_MAX_EVENTS", "10")), 25))
