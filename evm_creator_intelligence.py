"""Read-only deployer/creation evidence helpers."""
from __future__ import annotations
from dataclasses import dataclass
from evm_rpc import EVMRPCClient, EthereumRPCError

@dataclass(frozen=True)
class CreatorReport:
    token: str
    creation_transaction: str | None
    creator: str | None
    creation_block: int | None
    warnings: tuple[str, ...] = ()

def inspect_creator(rpc: EVMRPCClient, token_address: str, creation_transaction: str) -> CreatorReport:
    token = token_address.lower()
    if not isinstance(creation_transaction, str) or not creation_transaction.startswith("0x"):
        raise ValueError("creation_transaction must be a transaction hash")
    try:
        tx = rpc.get_transaction(creation_transaction)
        receipt = rpc.get_transaction_receipt(creation_transaction)
    except EthereumRPCError as exc:
        raise RuntimeError(f"Creator data unavailable: {exc}") from exc
    if not isinstance(tx, dict) or not isinstance(receipt, dict):
        raise RuntimeError("Invalid creation transaction response")
    creator = tx.get("from")
    contract = receipt.get("contractAddress")
    block_raw = receipt.get("blockNumber")
    if not isinstance(creator, str) or not isinstance(contract, str) or contract.lower() != token:
        return CreatorReport(token, creation_transaction, creator if isinstance(creator, str) else None, None, ("CREATION_TRANSACTION_TOKEN_MISMATCH",))
    try:
        block = int(block_raw, 16) if isinstance(block_raw, str) else int(block_raw)
    except (TypeError, ValueError):
        block = None
    return CreatorReport(token, creation_transaction, creator.lower(), block)
