from __future__ import annotations

import json
import urllib.error
import urllib.request

from models import Narrative


def _clean(text: str, limit: int = 180) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _newest_signal(narrative: Narrative):
    return max(narrative.signals, key=lambda item: item.published_at)


def format_trend(narrative: Narrative) -> str:
    signal = _newest_signal(narrative)
    title = _clean(narrative.title.title(), 120)
    topic = _clean(signal.text, 220)

    return (
        f"🔥 <b>TRENDING NOW</b>\n\n"
        f"<b>{title}</b>\n"
        f"{topic}\n\n"
        f"<b>Token creation potential</b>\n"
        f"• Narrative token: turn the current topic into a simple community/narrative token\n"
        f"• Utility angle: rewards, access, participation or community incentives around the trend\n"
        f"• Timing angle: the value proposition is strongest while this story is actively getting attention\n\n"
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
