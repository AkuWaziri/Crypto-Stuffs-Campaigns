# Crypto-Stuffs-Campaigns

Crypto-content discovery feed for Telegram.

## What it watches

The feed is now focused on one category only:

- **Funny/creative crypto content** — satire, parody, irony, jokes, memes, comics, humorous observations, funny crypto situations, shitposts and other genuinely humorous/creative crypto content.

All other content categories are sunset.

## Sources

- X/Twitter
- Reddit
- Medium
- Public Telegram channels
- Bluesky
- Farcaster

## Filtering

Every item must be crypto-related and match the **Funny/creative crypto content** category.

There is no quality score, signal score, ranking, campaign score, or campaign/reward classification.

## Current mode

Read-only. No wallet connections, trading, token creation or transaction execution.

## X scraper

X uses an authenticated web session supplied through GitHub Secrets.

Required secrets:
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- X_AUTH_TOKEN
- X_CT0

The GitHub Actions feed runs every 3 hours.

## Separate high-performance crypto lane

A separate discovery lane also searches X for high-performing crypto posts across niches including AI, AI agents, hacking/security, payments, DeFi, development, NFTs, nodes, infrastructure, on-chain findings, research, smart contracts, builders, protocols and wallets.

Only posts verified at **100,000+ views** are eligible for this lane. They are sent separately from the funny/creative crypto feed and are not required to match the funny/creative category.
