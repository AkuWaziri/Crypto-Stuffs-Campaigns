"""Live read-only Ethereum observation pipeline."""
from __future__ import annotations
import time
from dataclasses import dataclass
from ethereum_discovery import DexScreenerDiscovery, deduplicate_candidates
from ethereum_market_data import DexScreenerClient, select_best_pair
from evm_rpc import EVMRPCClient
from evm_contract_security import inspect_erc20
from evm_holder_intelligence import inspect_holders
from evm_early_buyer_intelligence import EarlyBuyerReport
from evm_funding_intelligence import FundingReport
from evm_cluster_intelligence import inspect_address_clusters
from evm_manipulation_intelligence import inspect_manipulation
from evm_qualification import qualify
from evm_behavior_intelligence import inspect_behavior
from evm_chain import ethereum_chain

@dataclass(frozen=True)
class Observation:
    symbol: str
    name: str
    contract: str
    dex: str
    market_cap_usd: float
    liquidity_usd: float
    score: int
    label: str
    hard_risks: tuple[str, ...]
    warnings: tuple[str, ...]
    signals: tuple[str, ...]
    explorer_url: str

def observe(rpc_url: str, query: str = "WETH", limit: int = 5, holder_window: int = 5000) -> list[Observation]:
    chain = ethereum_chain(rpc_url)
    rpc = EVMRPCClient(chain.rpc_url)
    discovery = DexScreenerDiscovery(DexScreenerClient())
    candidates = deduplicate_candidates(discovery.discover(query, max_results=max(limit * 3, limit)))
    now_ms = int(time.time() * 1000)
    try:
        latest_block = rpc.get_block_number()
    except Exception:
        latest_block = 0
    observations=[]
    for candidate in candidates[:limit]:
        try:
            market = select_best_pair(DexScreenerClient().token_pairs(candidate.contract), now_ms=now_ms)
            security = inspect_erc20(rpc, candidate.contract)
            if not latest_block:
                raise RuntimeError("latest block unavailable")
            holders = inspect_holders(rpc, candidate.contract, max(0, latest_block-holder_window), latest_block, excluded_addresses=[market.pair])
            early = EarlyBuyerReport(candidate.contract, 0, 0, (market.pair,), warnings=("EARLY_BUYER_LAUNCH_BLOCK_NOT_RESOLVED",))
            funding = FundingReport(candidate.contract, (), 0, 0, 0, warnings=("DEPLOYER_ANCHOR_NOT_RESOLVED",))
            cluster = inspect_address_clusters(holder_addresses=[h.address for h in holders.holders])
            behavior = inspect_behavior(market)
            manipulation = inspect_manipulation(market=market, security=security, holders=holders, early_buyers=early, funding=funding, cluster=cluster)
            manipulation = type(manipulation)(manipulation.hard_risks, tuple(sorted(set(manipulation.warnings)|set(behavior.warnings))), tuple(sorted(set(manipulation.signals)|set(behavior.signals))), manipulation.evidence_score)
            result = qualify(market=market, security=security, manipulation=manipulation)
            warnings=tuple(sorted(set(result.warnings)|set(holders.warnings)))
            observations.append(Observation(market.symbol, market.name, market.contract, market.dex, market.market_cap_usd, market.liquidity_usd, result.score, result.label, result.hard_risks, warnings, manipulation.signals, chain.explorer_url + "/address/" + market.contract))
        except Exception as exc:
            observations.append(Observation(candidate.contract, "", candidate.contract, candidate.dex or "unknown", 0, 0, 0, "INSUFFICIENT DATA", (str(exc),), (), (), chain.explorer_url + "/address/" + candidate.contract))
    return observations
