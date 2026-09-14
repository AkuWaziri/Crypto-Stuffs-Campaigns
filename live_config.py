import os


def env_list(name: str) -> list[str]:
    raw = os.getenv(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


SOLANA_WALLETS = env_list("SOLANA_WALLETS")
EVM_WALLETS = env_list("EVM_WALLETS")
EVM_CHAIN = os.getenv("EVM_CHAIN", "ethereum")
POLL_LIMIT = max(1, min(int(os.getenv("POLL_LIMIT", "20")), 100))
