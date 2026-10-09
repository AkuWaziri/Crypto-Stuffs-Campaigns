# Crypto-Stuffs-Campaigns

A read-only crypto intelligence feed and editorial research assistant delivered through Telegram.

## Current feed lanes

1. **Viral and trending crypto posts from X** across AI and agents, DeFi, stablecoins, payments, security, infrastructure, smart contracts, airdrops, hackathons, on-chain activity, builders, protocols and other crypto niches.
   - Only posts from accounts with an explicit X verification/checkmark flag in the response are eligible; unverified accounts are excluded.\n   - Looks back 7 days.
   - Trending threshold: 20,000+ views by default.
   - Viral tier: 50,000+ views.
2. **Practical crypto discoveries** from Google News RSS and GitHub repository search, including developer tools, guides, SDKs, APIs, automation, security research, dashboards, hackathon resources and infrastructure releases.

The scheduled run targets up to 30 feed items: up to 20 viral/trending posts and 10 practical discoveries, filling unused slots from remaining candidates where available. Thirty is a cap, not a guaranteed count.

## Per-post content recommendations

**Every individual feed message** now includes a topic-specific content recommendation, not just the separate editorial digest. Each recommendation includes:
- a differentiated angle for the finding's topic;
- a suggested opening hook to develop in your own voice;
- guidance on what to verify and how to add an interpretation, caveat, or practical takeaway.

Recommendations vary for security, stablecoin payments, DeFi, AI agents, developer tools, on-chain research, infrastructure, funding, and other crypto findings. They are writing direction, not claims that have already been verified. Use the linked source and, where possible, primary evidence before posting.

## Editorial intelligence

After successfully delivering new feed items, the bot sends a compact **Editorial Intelligence** digest for up to three strong leads. The digest gives each selected finding:
- a topic and source link, with a reminder to verify the underlying claim;
- **three differentiated angles**: technical mechanism, second-order implication, and builder/experiment angle;
- a **post scaffold** with placeholders for verified facts, interpretation, caveat, and test;
- a **Build Radar** mini-tool concept to validate against real user needs.

The angles are rule-based writing scaffolds, not a substitute for reading primary sources or independently verifying claims. The bot does not auto-publish social posts.

## Deduplication and delivery

- The discovery lanes filter previously sent IDs and content fingerprints using local JSON state.
- State is written after successful Telegram delivery.
- GitHub Actions runs the feed every 5 hours and uses Actions cache to restore the state file.
- Manual execution is available with workflow_dispatch.

## Safety and mode

- Read-only discovery. No wallet connections, trading, token creation, or transaction execution.
- Content is sent to Telegram for review; no automatic X publishing.
- X search uses the authenticated session configured through GitHub Actions secrets.

## Required GitHub Actions secrets

- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- X_AUTH_TOKEN
- X_CT0

## Local usage

    pip install -r requirements.txt
    python main.py --telegram
    python main.py --test
    pytest -q

The --test flag performs a dry run and prints messages instead of sending them.
