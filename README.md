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
