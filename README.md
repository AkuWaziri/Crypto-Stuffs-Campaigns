# Crypto-Stuffs-Campaigns

Crypto-content discovery feed for Telegram.

## What it watches

Only crypto-related content that is:
- Satirical or parody
- Ironic
- Funny or laughable
- Metaphorical or analogy-driven
- Research/data/experiment based
- Comic/cartoon/meme based
- An unusual or interesting finding/discovery

## Sources

- X/Twitter
- Reddit
- Medium
- Public Telegram channels
- Bluesky
- Additional public sources can be added through the source modules

## Filtering

Every item must be crypto-related and match at least one requested content form.

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
