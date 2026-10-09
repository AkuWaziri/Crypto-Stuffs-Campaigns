# Crypto-Stuffs-Campaigns

An automated crypto findings feed for Telegram. It scans public news and social sources and forwards up to 10 distinct, recent findings per run with the direct source link. No paid AI API key or generated rewrite is required.

## Coverage

- Exploits, security incidents, wallet movements, suspicious fund flows and on-chain investigations
- Protocol updates, builders, new tools, open-source projects, infrastructure and technical discoveries
- DeFi, stablecoins, payments, AI agents, adoption, airdrops, rewards, launches and governance
- Market anomalies, unexpected links between events, user losses and accountability stories

## Investigation standard

Prioritize stories where the source provides a concrete finding, unusual pattern, meaningful numbers, a timeline or a connection worth following. When assessing a story, verify important numbers, timelines, source claims and links wherever possible; compare claims with on-chain evidence, follow wallet movements and trace connections between events when reliable public data is available. Do not present unverified allegations or inferred links as established facts.

The bot forwards the source material and its direct URL so the user can follow the link and investigate independently. It does not generate rewritten commentary or research assignments.

## Sources

- X search for high-performing crypto posts
- Google News RSS
- GitHub repository search
- Medium RSS
- Reddit public search
- Bluesky public search
- Farcaster public search
- Optional public Telegram channels configured in `TELEGRAM_CHANNELS`

Source availability varies; platforms may rate-limit or block automated requests.

## Schedule and delivery

GitHub Actions runs every 3 hours (UTC cron schedule) and supports manual runs. The feed sends up to 10 new findings per run and checks a 7-day lookback. Deduplication state persists across runs, and items are marked as sent only after Telegram accepts delivery.

## Required GitHub Actions secrets

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `X_AUTH_TOKEN`
- `X_CT0`

Read-only discovery only. No wallet connections, trading or transaction execution.
