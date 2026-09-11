# TrendsBot

Crypto trend intelligence and Solana token-launch research engine.

## Current mode

**TEST / READ-ONLY**

The first phase only discovers and scores very recent crypto narratives. It does not create tokens, trade, buy, sell, or move funds.

## Architecture

1. Source registry
2. Fresh-signal collection
3. Timestamp/freshness validation
4. Topic extraction
5. Narrative clustering
6. Trend scoring
7. Solana/on-chain verification
8. Token concept qualification
9. Launch engine (future, disabled until explicitly enabled)
10. Post-launch monitoring (future)

## Hard constraints

- Maximum 2 launches per decision cycle in production
- No self-buying
- No automated trading
- No wash trading or artificial volume
- Launch functionality remains disabled during intelligence development
- Secrets are supplied through GitHub Actions secrets, never committed to the repository
