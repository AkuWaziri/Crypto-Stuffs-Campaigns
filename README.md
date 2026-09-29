# Crypto-Stuffs-Campaigns

Crypto-content discovery feed for Telegram.

## What it watches

The feed is intentionally broad: **crypto + something worth seeing**.

It surfaces crypto-related:
- Satire, parody, irony, jokes, memes and comics
- Metaphors, analogies and unusual observations
- Research, data, experiments, investigations and findings
- Things people are actively building, shipping or prototyping
- Product, app and protocol ideas
- Technical architecture, mechanisms, primitives and infrastructure
- Open-source repos, SDKs, libraries and developer tools
- Hackathon builds, demos, MVPs, alpha and beta experiments
- UX, onboarding, wallets, payments and other crypto product design
- Problems, pain points and unmet needs worth solving
- Integrations across crypto, AI, DePIN, gaming, social, identity and payments
- Real-world crypto applications and new use cases

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
