"""AI editorial layer for source-linked crypto findings."""
import json
import os
from functools import lru_cache
from pathlib import Path

from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DNA_PATH = Path(__file__).with_name("DNA.md")
BASE_PROMPT = """You are the editorial writer for a crypto-native research and discovery feed.
Write in the user's human writing DNA, defined in the repository's DNA.md style guide.
Use the DNA guide as editorial instructions, not as factual source material.
Never invent facts, numbers, wallet identities, motives, connections, timelines or on-chain verification.
Distinguish observed transaction evidence from claims about intent or ownership. Attribute allegations.
Do not claim you independently opened or verified the linked source. The user will investigate manually.
Always finish with a separate line containing the exact original URL: Source: <the exact original URL>.
Return only the finished Telegram-ready finding. Do not add an AI-summary heading or explain your process."""


@lru_cache(maxsize=1)
def _system_prompt():
    """Load the editable human writing DNA file, with a safe fallback."""
    try:
        dna = DNA_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        dna = (
            "Lead with the surprising, specific finding. Tell a compact story with "
            "concrete details, natural crypto-native phrasing and a blunt observation "
            "when earned. Avoid generic AI language, forced slang, repetition and "
            "unsupported claims. Keep the original source URL."
        )
    return f"{BASE_PROMPT}\n\n--- HUMAN WRITING DNA ---\n{dna}"


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
            {"role": "system", "content": _system_prompt()},
            {
                "role": "user",
                "content": (
                    "Write a source-linked crypto finding from this material. "
                    "Lead with the finding rather than mechanically rewriting a headline. "
                    "Use only facts present in the material; do not invent missing context. "
                    "Preserve the exact original URL on the final Source line.\n\n"
                    + json.dumps(source_material, ensure_ascii=False)
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
