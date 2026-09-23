# Crypto-Stuffs-Campaigns

Crypto campaign and trend intelligence feed for Telegram.

## What it watches

- X/Twitter crypto campaigns and announcements
- Airdrops and points programs
- Creator, video, meme and art competitions
- Builder, hackathon, testnet and mainnet opportunities
- IDO/token sales and NFT campaigns
- Grants, bounties and ambassador programs
- Public campaign/quest platforms such as Zealy, Galxe and Layer3
- Emerging crypto topics and narratives

## Current mode

Read-only. No wallet connections, trading, token creation or transaction execution.

## X scraper

The first implementation uses twscrape with an authenticated X session supplied through GitHub Secrets. X session availability can change because X actively changes its web interface and anti-bot controls.

Required secrets:

- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- X_AUTH_TOKEN
- X_CT0

The scheduled feed runs hourly. Use GitHub Actions manual dispatch for testing.
