from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.request

from models import Narrative


def _clean(text: str, limit: int = 260) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _newest_signal(narrative: Narrative):
    return max(narrative.signals, key=lambda item: item.published_at)


def _headline(narrative: Narrative) -> str:
    """Build a compact readable headline without adding analysis or recommendations."""
    signal = _newest_signal(narrative)
    text = " ".join(signal.text.split())
    text = re.sub(r"https?://\S+", "", text).strip()
    text = re.sub(r"\s+", " ", text)

    # Prefer the first sentence when it is substantial enough to work as a headline.
    first_sentence = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0].strip()
    headline = first_sentence if 20 <= len(first_sentence) <= 110 else text
    return _clean(headline, 110)


def format_trend(narrative: Narrative, number: int | None = None) -> str:
    signal = _newest_signal(narrative)
    raw_text = " ".join(signal.text.split())
    raw_text = re.sub(r"https?://\S+", "", raw_text).strip()
    headline_raw = _headline(narrative)
    remainder = raw_text[len(headline_raw):].strip() if raw_text.startswith(headline_raw) else raw_text

    headline = html.escape(headline_raw)
    label = f"<b>{number}. {headline}</b>" if number is not None else f"<b>{headline}</b>"
    body = f"\n{html.escape(_clean(remainder, 260))}" if remainder else ""

    return (
        f"{label}{body}\n\n"
        f"🔗 <a href=\"{html.escape(signal.url, quote=True)}\">Source</a>"
    )


def format_feed(narratives: list[Narrative], max_items: int = 5) -> str:
    if not narratives:
        return "📰 <b>CRYPTO TRENDS</b>\n\nNo fresh crypto trends found in this cycle."

    ordered = sorted(
        narratives,
        key=lambda item: _newest_signal(item).published_at,
        reverse=True,
    )[:max_items]

    items = [format_trend(item, index) for index, item in enumerate(ordered, start=1)]
    return "📰 <b>CRYPTO TRENDS</b>\n\n" + "\n\n━━━━━━━━━━━━━━━━━━━━\n\n".join(items)


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
