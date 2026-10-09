# Crypto-Stuffs-Campaigns

A read-only crypto intelligence feed and editorial research assistant delivered through Telegram.

## Current feed lanes

1. **Viral and trending crypto posts from X** across AI and agents, DeFi, stablecoins, payments, security, infrastructure, smart contracts, airdrops, hackathons, on-chain activity, builders, protocols and other crypto niches.
   - Looks back 7 days.
   - Trending threshold: 20,000+ views by default.
   - Viral tier: 50,000+ views.
2. **Practical crypto discoveries** from Google News RSS and GitHub repository search, including developer tools, guides, SDKs, APIs, automation, security research, dashboards, hackathon resources and infrastructure releases.

The scheduled run targets up to 30 feed items: up to 20 viral/trending posts and 10 practical discoveries, filling unused slots from remaining candidates where available. Thirty is a cap, not a guaranteed count.

## Editorial intelligence (new)

After successfully delivering new feed items, the bot sends a compact **Editorial Intelligence** digest for up to three of the strongest leads. It includes:
- topic classification and source link;
- a prompt to verify the claim and identify what remains uncertain;
- an angle for a technical or practical explanation;
- a **Build Radar** mini-tool concept to validate against real user needs;
- a repeatable human review checklist.

This layer is intentionally transparent and heuristic-based. It does not pretend that a headline is verified, does not generate fabricated evidence, and does not auto-publish social posts. Treat its angles and build ideas as starting points for investigation.

## Deduplication and delivery

- The discovery lanes filter previously sent IDs and content fingerprints using local JSON state.
- State is written after successful Telegram delivery.
- GitHub Actions runs the feed every 5 hours and uses Actions cache to restore the state file.
- Manual execution is available with `workflow_dispatch`.

## Safety and mode

- Read-only discovery. No wallet connections, trading, token creation, or transaction execution.
- Content is sent to Telegram for review; no automatic X publishing.
- X search uses the authenticated session configured through GitHub Actions secrets.

## Required GitHub Actions secrets

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `X_AUTH_TOKEN`
- `X_CT0`

## Local usage

```bash
pip install -r requirements.txt
python main.py --telegram
python main.py --test
pytest -q
```

`--test` performs a dry run and prints messages instead of sending them.
