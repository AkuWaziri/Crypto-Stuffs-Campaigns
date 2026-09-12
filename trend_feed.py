from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from models import Narrative


def _clean(text: str, limit: int = 180) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _newest_signal(narrative: Narrative):
    return max(narrative.signals, key=lambda item: item.published_at)


def _topic_text(narrative: Narrative) -> str:
    return " ".join([narrative.title, *[signal.text for signal in narrative.signals]]).lower()


def _token_angles(narrative: Narrative) -> tuple[str, str, str]:
    """Return simple, topic-specific token concepts without scoring or execution."""
    text = _topic_text(narrative)

    if any(term in text for term in ("airdrop", "airdrop campaign", "claim")):
        return (
            "Narrative token: turn the campaign moment into a community token for participants",
            "Utility angle: points, claim milestones, quests or community access can anchor demand",
            "Timing angle: the concept is strongest while participation and attention are active",
        )

    if any(term in text for term in ("stablecoin", "payments", "payment", "usdc", "usdt")):
        return (
            "Narrative token: build around the payment rail or stablecoin adoption story",
            "Utility angle: rewards, merchant/community incentives or access can connect the token to usage",
            "Timing angle: adoption announcements create the clearest window for a community narrative",
        )

    if any(term in text for term in ("defi", "lending", "liquidity", "yield", "dex", "staking")):
        return (
            "Narrative token: package the protocol or DeFi theme into a community-owned narrative",
            "Utility angle: governance, participation rewards or access can give the token a defined role",
            "Timing angle: attention is strongest while usage, launches or liquidity events are accelerating",
        )

    if any(term in text for term in ("bitcoin", "btc", "ethereum", "eth", "solana", "sol", "base", "arbitrum")):
        return (
            "Narrative token: turn the ecosystem story into a simple community/narrative token",
            "Utility angle: community access, participation rewards or ecosystem campaigns can support it",
            "Timing angle: the strongest window is when the ecosystem story is actively spreading",
        )

    if any(term in text for term in ("ai agent", "ai agents", "crypto agent", "crypto agents", "agent")):
        return (
            "Narrative token: build around the AI-agent story as a community coordination layer",
            "Utility angle: access, agent tasks, reputation or participation rewards can define the role",
            "Timing angle: the concept benefits most while the agent narrative is gaining attention",
        )

    return (
        "Narrative token: turn the current crypto story into a simple community/narrative token",
        "Utility angle: rewards, access, participation or community incentives can give it a clear role",
        "Timing angle: the concept is strongest while this story is actively getting attention",
    )


def format_trend(narrative: Narrative) -> str:
    signal = _newest_signal(narrative)
    title = _clean(narrative.title.title(), 120)
    topic = _clean(signal.text, 220)
    angle_one, angle_two, angle_three = _token_angles(narrative)

    return (
        f"🔥 <b>TRENDING NOW</b>\n\n"
        f"<b>{title}</b>\n"
        f"{topic}\n\n"
        f"<b>Token creation potential</b>\n"
        f"• {angle_one}\n"
        f"• {angle_two}\n"
        f"• {angle_three}\n\n"
        f"🔗 <a href=\"{signal.url}\">Source</a>\n"
        f"<i>READ-ONLY · NO TOKEN CREATED</i>"
    )


def format_feed(narratives: list[Narrative], max_items: int = 5) -> str:
    if not narratives:
        return "📰 <b>CRYPTO TREND FEED</b>\n\nNo fresh crypto trends found in this cycle."

    ordered = sorted(
        narratives,
        key=lambda item: _newest_signal(item).published_at,
        reverse=True,
    )
    return "\n\n━━━━━━━━━━━━━━━━━━━━\n\n".join(
        format_trend(item) for item in ordered[:max_items]
    )


def send_telegram(text: str, bot_token: str, chat_id: str) -> None:
    if not bot_token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required")

    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                raise RuntimeError(f"Telegram returned HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Telegram returned HTTP {exc.code}: {body}") from exc
