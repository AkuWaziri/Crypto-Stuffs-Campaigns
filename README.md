# Crypto-Stuffs-Campaigns

An automated crypto intelligence feed for Telegram. It searches public news and social sources, identifies concrete developments and unusual patterns, then delivers concise, human-sounding findings with links to the underlying source.

## What it looks for

- Exploits, security incidents, wallet clusters, suspicious fund flows and on-chain investigations
- Protocol updates, builders, new tools, open-source projects, infrastructure and technical discoveries
- DeFi, stablecoins, payments, AI agents, adoption, airdrops, rewards, launches and governance
- Market anomalies and unexpected connections between crypto events
- Costly mistakes, user losses, compensation decisions and accountability stories

## Writing standard

The feed should sound like a knowledgeable crypto-native person who found something interesting, checked the details and wants to explain it naturally. Lead with the finding, preserve concrete numbers and timelines, explain the sequence, and use irony or sarcasm only when it fits. Avoid generic news intros, corporate summaries, forced slang, engagement bait and repetitive templates. Never invent wallet attribution, motives, numbers or causal links. Keep allegations attributed and uncertainty clear.

Each Telegram message contains the finished finding and a source link. It does not send research assignments, writing suggestions or editorial recommendations.

## Sources

- X search for high-performing crypto posts
- Google News RSS
- GitHub repository search
- Medium RSS
- Reddit public search
- Bluesky public search
- Farcaster public search
- Optional public Telegram channels configured in `TELEGRAM_CHANNELS`

Source availability varies; Reddit and other platforms may rate-limit or block automated requests.

## Schedule and delivery

GitHub Actions runs every 5 hours and supports manual runs. The feed sends up to 30 new findings per run and checks a 7-day lookback. Deduplication state persists across runs, and items are marked as sent only after Telegram accepts delivery.

## Model-assisted writing

For the full human-tone rewrite, configure these GitHub Actions repository secrets/variables:

- Secret `OPENAI_API_KEY`: API key for an OpenAI-compatible chat-completions endpoint
- Optional variable `OPENAI_BASE_URL`: defaults to `https://api.openai.com/v1`
- Optional variable `OPENAI_MODEL`: defaults to `gpt-4o-mini`

Without an API key, the bot remains operational and forwards source text with its source link, but cannot produce the model-assisted rewrite.

## Required GitHub Actions secrets

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `X_AUTH_TOKEN`
- `X_CT0`

Read-only discovery only. No wallet connections, trading or transaction execution.
