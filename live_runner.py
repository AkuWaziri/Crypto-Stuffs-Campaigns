"""CLI entrypoint for scheduled read-only Ethereum observation."""
from __future__ import annotations
import os
from live_observation import observe
from telegram_output import format_feed, send_telegram

def main() -> None:
    rpc_url=os.environ["ETH_RPC_URL"]
    query=os.getenv("EVM_DISCOVERY_QUERY","WETH")
    limit=int(os.getenv("EVM_OBSERVATION_LIMIT","5"))
    observations=observe(rpc_url, query=query, limit=limit)
    send_telegram(format_feed(observations))
    print(f"observations={len(observations)}")

if __name__ == "__main__": main()
