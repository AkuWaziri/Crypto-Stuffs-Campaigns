# WhalesBoarder

Read-only intelligence system for tracking large wallet and institutional activity across crypto and stocks.

## Scope

- Solana
- EVM chains
- Publicly disclosed stock activity
- Large wallets, known funds, organizations, protocol treasuries, market makers, and other labeled entities
- Telegram as the primary feed
- Explain **why** a buy or sell may be happening when evidence exists

## Rules

1. A transfer is not automatically a buy or sell.
2. Crypto buys/sells require transaction-direction evidence such as a swap or equivalent market interaction.
3. Stock activity is based on public disclosures and market/flow data; it is not assumed to be real-time.
4. Reasons are evidence-ranked:
   - `CONFIRMED` — directly supported by evidence
   - `INFERRED` — plausible and supported by surrounding evidence
   - `UNKNOWN` — no reliable reason identified
5. No trade execution, no order placement, and no token launching.

## Initial architecture

`source -> normalize -> classify -> explain -> Telegram`

Provider integrations will be added without changing the normalized event model.

## Status

Foundation reset complete. Crypto monitoring is the first implementation target, starting with Solana and EVM.
