# Ethereum token-launch research framework

## Purpose

This document turns external research into engineering requirements for the read-only Ethereum intelligence bot. Research is evidence for feature design, not a substitute for independent validation or a trading signal.

## Research that materially informs the system

### 1. Chainalysis: Ethereum pump-and-dump / rug-pull patterns

Chainalysis studied Ethereum token launches and identified recurring on-chain patterns around traction, concentrated liquidity removal, creator behavior, and abrupt market failure. Their 2023 analysis found roughly 370,000 tokens launched on Ethereum, about 168,600 listed on a DEX, and about 90,408 tokens matching their specific liquidity-removal pattern. Their methodology is explicitly a way to prioritize suspicious patterns, not proof that every matched token was illicit.

Engineering implications:
- Track launch time and time-to-traction.
- Track liquidity at launch and over time.
- Track liquidity-provider identity and removal percentage.
- Track creator/deployer and related-wallet behavior.
- Track early trading activity rather than relying on price alone.
- Treat liquidity removal as a high-value risk event.
- Never label a token a confirmed scam solely from a statistical pattern.

### 2. Chainalysis: 2024 market-manipulation methodology

Chainalysis later tightened its suspected pump-and-dump methodology around a liquidity provider removing at least 65% of pool liquidity, the pool becoming inactive, and prior traction above 100 transactions. This is useful as a research feature family, but the thresholds should remain calibration inputs rather than hard-coded truth.

Engineering implications:
- Record liquidity-removal events as time-series observations.
- Record pool transaction counts before removal.
- Compare current liquidity with launch/peak liquidity.
- Preserve raw observations so thresholds can be recalibrated later.

### 3. TokenScout: temporal graph learning for Ethereum scam detection

TokenScout is a 2026 peer-reviewed research result using temporal attributed transaction graphs for early scam-token detection. The paper reports a balanced accuracy of 98.41% on a dataset of 214,084 ERC-20 tokens and reports Ethereum deployment results identifying rugpulls, honeypots, and Ponzi schemes. The result is promising but must not be treated as a production guarantee: dataset construction, label quality, time leakage, chain changes, and distribution shift all matter.

Engineering implications:
- Preserve temporal wallet/token relationships rather than only static holder percentages.
- Build reusable transaction graphs for deployer, early buyers, funders, sellers, and liquidity participants.
- Keep an observation timestamp/window with every derived metric.
- Do not train a model until deterministic features and labels are available.
- Keep a non-ML rules baseline so model output can be audited.

### 4. DexScreener as market/discovery infrastructure

DexScreener provides public API endpoints for pair search, token-pair lookup, pair details, transaction counts, volume, price change, liquidity, FDV, market cap, and pair creation time. It is therefore suitable as one market-data source, not as the sole source of truth.

Engineering implications:
- Canonical identity remains the Ethereum contract address.
- Validate `chainId` before accepting a pair.
- Cross-check market fields and reject impossible/contradictory values.
- Prefer the most liquid usable pair while retaining the other pairs for later liquidity analysis.
- Do not use paid boosts, trending placement, or social metadata as proof of quality.

## Decision-making model for this bot

The bot should not answer only `ape / don't ape`. It should progressively answer:

1. **DISCOVERED** — token exists and was found through a legitimate source.
2. **MARKET-USABLE** — usable Ethereum market data exists and passes validation.
3. **CONTRACT-SAFE / CONTRACT-RISK** — Stage 3 security analysis.
4. **LIQUIDITY-SAFE / LIQUIDITY-RISK** — pool ownership, concentration, and removal analysis.
5. **HOLDER / FLOW PROFILE** — concentration, early buyers, participation and wallet relationships.
6. **CORE-QUALIFIED** — deterministic core score passes without critical hard-risk failure.
7. **ADVANCED-PENDING** — enough time/transactions have not yet accumulated for advanced analysis.
8. **MATURE-QUALIFIED** — core plus advanced evidence passes.
9. **REJECTED / DATA INSUFFICIENT / PROVIDER FAILURE** — these must remain distinct.

## Evidence hierarchy

Hard security and control evidence outranks momentum. A token with strong volume, buys, and price momentum must not pass a critical contract or liquidity-control failure.

A useful ordering is:

`contract control -> sellability -> liquidity control -> holder/flow concentration -> deployer behavior -> market quality -> momentum`

Momentum is evidence of market activity, not evidence of safety.

## Research-derived features to collect

### Launch
- deployment block and timestamp
- deployer
- first DEX pair
- first liquidity event
- time from deployment to first liquidity
- time from liquidity to first meaningful trading

### Market
- price
- market cap
- FDV
- liquidity
- liquidity/market-cap
- 5m/1h volume
- 5m/1h buys and sells
- buy/sell ratios
- 5m/1h price change
- pair age
- multi-pair liquidity

### Security
- source verification
- proxy and implementation
- owner/administrator privileges
- mint/burn controls
- blacklist/whitelist
- pause/trading controls
- max wallet / max transaction
- transfer and buy/sell taxes
- fee-changing authority
- arbitrary balance modification
- sell simulation where supported

### Wallet intelligence
- top-holder concentration
- deployer holdings and sales
- early buyer count
- early buyer concentration
- repeated wallets
- common-funder relationships
- observed participation growth
- liquidity-provider concentration
- liquidity removal events

## Calibration rule

Research thresholds are engineering defaults until the bot has collected enough observations. We will keep raw observations and outcomes, then evaluate whether each rule actually improves decision quality. Threshold changes should be deliberate and versioned, not continuously tuned to recent winners.

## Important implementation constraint

External research APIs are not automatically approved for production integration. Each provider must be checked for current documentation, rate limits, licensing/terms, cost, and whether its intended use is compatible with this bot. Research findings can be implemented from first principles using Ethereum RPC and permitted market-data APIs even when a third-party security service is not suitable for direct integration.
