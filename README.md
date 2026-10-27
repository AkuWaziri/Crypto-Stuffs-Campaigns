# Crypto-Stuffs-Campaigns

An automated AI-written crypto findings feed for Telegram. It scans public news and social sources, uses Groq to research and turn the strongest new items into concise, human-sounding findings, and includes the original source link for manual follow-up. It sends up to 10 distinct findings per run.

## Editorial style

The AI writer follows the user's writing DNA:
- Lead with the finding and concrete details, not generic scene-setting.
- Tell a compact, evidence-led story and explain what is unusual or why it matters.
- Use natural crypto-native phrasing, contractions, blunt observations and occasional dry sarcasm when earned.
- Vary openings and rhythm. Avoid corporate language, generic AI phrasing, fake hype, forced slang and filler.
- Never invent numbers, wallet identities, motives, connections or verification. Attribute allegations and distinguish observed evidence from interpretations.
- Preserve the exact source URL at the end of every finding.

The research pipeline attempts to retrieve article text and resolve Google News wrappers to direct publisher URLs when possible. It distinguishes source claims from verified facts and does not claim independent verification unless the relevant evidence was actually checked. A deterministic triage score helps prioritize candidates for research; it is not a truth or confidence score. A bounded research audit trail records candidate scores, content type, publication status, and skip/error reasons across scheduled runs. Weak findings are skipped. Before delivery, a conservative consistency gate holds drafts containing concrete numbers or wallet/contract addresses absent from the retrieved source text; this checks draft-to-source consistency, not whether the source itself is true. The manually triggered Research Dry Run workflow retrieves current sources, uses a maximum of three Groq calls, sends nothing to Telegram, and uploads an audit-record artifact for review. The editorial engine uses distinct research instructions for investigations, tokenomics/protocol analysis, breaking developments, developer tools, and education; practical guides and skill-showcase posts retain their dedicated workflows.

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

GitHub Actions runs every 5 hours (UTC cron schedule) and supports manual runs. The feed sends up to 10 new findings per run and checks a 7-day lookback. Deduplication state persists across runs, and items are marked as sent only after Telegram accepts delivery.

## Required GitHub Actions secrets

- `GROQ_API_KEY` — used by the research and editorial model
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `X_AUTH_TOKEN`
- `X_CT0`

The scheduled workflow uses `openai/gpt-oss-20b` through Groq; override `GROQ_MODEL` to change it. If Groq is unavailable or the per-run model-call budget is exhausted, candidates are held or skipped rather than publishing generic, unreviewed fallback drafts. Original source links are preserved, and Google News links are resolved to publisher URLs when redirects expose them.

Read-only discovery only. No wallet connections, trading or transaction execution.
