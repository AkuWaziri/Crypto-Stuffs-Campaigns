# Crypto-Stuffs-Campaigns

An automated AI-written crypto findings feed for Telegram. It scans public news and social sources, uses OpenAI to turn the strongest new items into concise, human-sounding findings, and includes the original source link for manual follow-up. It sends up to 10 distinct findings per run.

## Editorial style

The AI writer follows the user's writing DNA:
- Lead with the finding and concrete details, not generic scene-setting.
- Tell a compact, evidence-led story and explain what is unusual or why it matters.
- Use natural crypto-native phrasing, contractions, blunt observations and occasional dry sarcasm when earned.
- Vary openings and rhythm. Avoid corporate language, generic AI phrasing, fake hype, forced slang and filler.
- Never invent numbers, wallet identities, motives, connections or verification. Attribute allegations and distinguish observed evidence from interpretations.
- Preserve the exact source URL at the end of every finding.

The bot writes from the discovered source material; it does not claim to have independently verified a source it has not opened. The user follows the original link for deeper manual research.

## Coverage

- Breaking crypto news, emerging narratives and market anomalies
- Exploits, security incidents, wallet movements, suspicious fund flows and on-chain investigations
- Protocol updates, builders, new tools, open-source projects, infrastructure and technical discoveries
- DeFi, stablecoins, payments, AI agents, adoption, airdrops, rewards, launches and governance
- User losses, accountability stories, unusual behavior and meaningful links between events

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

- `OPENAI_API_KEY` — used by the AI writer
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `X_AUTH_TOKEN`
- `X_CT0`

The default model is `gpt-4o-mini`; override with `OPENAI_MODEL` if needed. OpenAI API usage is billed separately from a ChatGPT subscription. If the AI call fails, the bot logs the error and forwards the original source material with its direct link as a fallback.

Read-only discovery only. No wallet connections, trading or transaction execution.
