"""AI editorial layer for source-linked crypto findings."""
import os
from functools import lru_cache

from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """You are the editorial writer for a crypto-native research and discovery feed.
Write in the user's human writing DNA:
- Lead with the actual finding, not a generic setup.
- Use concrete numbers, names, dates, transaction details and contrasts when they are present in the supplied source material.
- Tell a compact, evidence-led story. Explain what is unusual and why it matters.
- Sound like a sharp crypto-native human: natural phrasing, contractions, blunt observations, occasional dry sarcasm when earned, varied openings and rhythm.
- Avoid corporate language, generic AI phrases, fake hype, forced slang, emoji filler and repetitive templates.
- Never invent facts, numbers, wallet identities, motives, connections, timelines or on-chain verification.
- Distinguish observed transaction evidence from claims about intent or ownership. Attribute allegations to the source.
- If the supplied material is thin, write a short, direct finding without padding or pretending it is deeper than it is.
- Do not claim you independently opened or verified the linked source. The user will investigate manually.
- Keep the write-up concise, usually 2-5 sentences. It should read like a finding worth clicking into, not a news headline rewrite.
- Always finish with a separate line: Source: <the exact original URL>.
Return only the finished Telegram-ready finding. Do not add a heading like 'AI summary' or explain your process."""


@lru_cache(maxsize=1)
def _client():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY secret is missing")
    return OpenAI(api_key=key)


def write_finding(item):
    """Write one evidence-conscious, human-sounding finding and preserve its source URL."""
    url = str(item.get("url") or "").strip()
    if not url:
        raise ValueError("Cannot write a finding without a source URL")

    source_material = {
        "source": item.get("source", "unknown"),
        "author": item.get("author", "unknown"),
        "published_or_seen_at": item.get("created_at", "unknown"),
        "views": item.get("views"),
        "category_or_niche": item.get("niche", ""),
        "source_text": str(item.get("text") or "").strip()[:7000],
        "original_url": url,
    }
    response = _client().chat.completions.create(
        model=MODEL,
        temperature=0.7,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Write a source-linked crypto finding from this material. "
                    "Use only facts present in the material; do not invent missing context. "
                    "Preserve the exact original URL on the final Source line.\n\n"
                    + __import__("json").dumps(source_material, ensure_ascii=False)
                ),
            },
        ],
    )
    text = (response.choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError("OpenAI returned an empty finding")
    # Enforce the exact link even if the model omitted or altered it.
    text = text.replace(url, "").strip()
    text = text.removesuffix("Source:").strip()
    return f"{text}\n\nSource: {url}" if text else f"{source_material['source_text']}\n\nSource: {url}"
