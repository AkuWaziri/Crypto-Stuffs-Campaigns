# Ethereum Bot

Read-only Ethereum token intelligence and qualification system.

## Mission

DISCOVER → ANALYZE → SCORE → RISK-CHECK → QUALIFY → REPORT TO TELEGRAM

The system is research-only. It never trades, buys, sells, swaps, approves, signs, submits transactions, loads private keys, or connects wallets.

## Initial scope

- Ethereum mainnet
- ERC-20 / ERC-20-compatible tokens
- DEX and on-chain discovery
- Market structure and liquidity analysis
- Contract and authority safety
- Holder and early-buyer intelligence
- Funding and deployer intelligence
- Participation and manipulation warnings
- Core and mature qualification pools
- Telegram reporting

## Current stage

### Stage 1 — Foundation

- Mainnet-only configuration
- Read-only Ethereum JSON-RPC client
- Bounded RPC cache
- Execution/signing RPC methods blocked
- Unit tests and GitHub Actions test workflow

### Stage 2 — Discovery + market data

- Canonical token identity is the Ethereum contract address
- DexScreener is implemented as one public market/discovery source
- Ethereum on-chain `PairCreated` discovery is implemented behind configurable factory/topic settings
- Candidates are deduplicated by contract address
- Market fields are normalized and validated fail-closed
- Provider failures are distinct from invalid/risky data
- No Solana-specific discovery logic is reused here

## Research foundation

`research/ethereum_launch_research.md` records the external evidence being translated into deterministic engineering features. It includes Chainalysis launch/manipulation studies and the 2026 TokenScout temporal-graph research. Research thresholds remain calibration inputs until the bot collects enough observations.

## Safety principles

- Missing important evidence fails closed
- Critical contract security failures override momentum and market score
- Provider failures are reported separately from risk rejection
- Observed participation is never presented as complete global history unless coverage supports that claim
- No execution capability is included
- External APIs are reviewed for current documentation, limits, terms, and suitability before production integration

Development proceeds in stages. Each stage is implemented, tested, inspected, and preserved before the next stage is added.
