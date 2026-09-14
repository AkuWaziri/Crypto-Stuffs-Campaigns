# WhalesBoarder

Read-only intelligence system for tracking large wallet and institutional activity across crypto and stocks.

## Scope

- Solana
- EVM chains
- Publicly disclosed stock activity
- Large wallets, known funds, organizations, protocol treasuries, market makers, and other labeled entities
- **Historically successful buyers** — wallets that bought assets that later produced strong realized ROI can qualify even when they are not currently among the largest holders
- Telegram as the primary feed
- Explain **why** a buy or sell may be happening when evidence exists

## What counts as a whale

Whale status is not based only on current wallet size. A wallet/entity can qualify through either:

1. **Size:** significant current holdings or transaction value.
2. **Track record:** demonstrated historical success from completed buy/sell activity, measured using realized ROI.

The second category is important because a smaller wallet with a strong record of identifying high-performing coins may be more useful to track than a large wallet that mainly holds assets passively.

Historical ROI is only reported when the available transaction history supports a completed position calculation. Open positions require a current market price before an unrealized ROI can be stated.

## Rules

1. A transfer is not automatically a buy or sell.
2. Crypto buys/sells require transaction-direction evidence such as a swap or equivalent market interaction.
3. Stock activity is based on public disclosures and market/flow data; it is not assumed to be real-time.
4. Reasons are evidence-ranked:
   - `CONFIRMED` — directly supported by evidence
   - `INFERRED` — plausible and supported by surrounding evidence
   - `UNKNOWN` — no reliable reason identified
5. ROI must be calculated from observed trade data; it must not be guessed from a token's chart alone.
6. No trade execution, no order placement, and no token launching.

## Initial architecture

`source -> normalize -> classify -> profile -> explain -> Telegram`

Provider integrations will be added without changing the normalized event model.

## Status

Foundation reset complete. Crypto monitoring is the first implementation target, starting with Solana and EVM. Whale qualification now supports both wallet size and historical realized ROI.
