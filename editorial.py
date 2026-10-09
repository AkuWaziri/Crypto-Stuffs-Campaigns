"""AI editorial layer for clean, source-linked crypto findings."""
import json
import os
from functools import lru_cache
from html import unescape
from pathlib import Path

from bs4 import BeautifulSoup
from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DNA_PATH = Path(__file__).with_name("DNA.md")
BASE_PROMPT = """You are the editorial writer for a crypto-native research and discovery feed.
Write in the user's human writing DNA, defined in DNA.md. Treat it as style guidance, not factual source material.
OUTPUT RULES:
- Write in clear, natural English. Translate non-English source text and headlines into English; preserve names, tickers, technical terms and exact numbers.
- Produce a useful finding, not a scraped title plus a copied snippet. Lead with the concrete discovery and explain what the project, event, technique or claim actually is.
- When the supplied evidence supports it, include a concise "Why it matters:" sentence explaining the practical implication, opportunity, risk or lesson. Do not force this section when the material is too thin.
- For project/repository discoveries, state what the project claims to do and why a crypto builder might investigate it. Do not imply that features work or code quality is verified unless the material proves that.
- Never include HTML/XML tags, RSS markup, image tags, "continue reading" boilerplate, raw webpage fragments or duplicate source links.
- Use only facts present in the supplied material. Never invent facts, numbers, wallet identities, motives, connections, timelines or on-chain verification. Attribute allegations and distinguish claims from verified facts.
- Do not claim you independently opened or verified the linked source.
- Keep the finding compact, usually 2–5 sentences, with varied natural wording. Avoid generic AI filler, corporate hype, forced slang, emoji decoration and repetitive templates.
- Always finish with a separate line containing the exact original URL: Source: <the exact original URL>.
Return only the finished Telegram-ready finding. Do not add an AI-summary heading or explain your process."""


def clean_source_text(value):
    """Strip HTML/XML markup and decode entities before editorial generation or fallback delivery."""
    raw = unescape(str(value or ""))
    soup = BeautifulSoup(raw, "html.parser")
    for node in soup(["script", "style", "noscript"]):
        node.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


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
    """Write one evidence-conscious, English-language finding and preserve its source URL."""
    url = str(item.get("url") or "").strip()
    if not url:
        raise ValueError("Cannot write a finding without a source URL")

    source_material = {
        "source": item.get("source", "unknown"),
        "author": item.get("author", "unknown"),
        "published_or_seen_at": item.get("created_at", "unknown"),
        "views": item.get("views"),
        "category_or_niche": item.get("niche", ""),
        "source_text": clean_source_text(item.get("text"))[:7000],
        "original_url": url,
    }
    response = _client().chat.completions.create(
        model=MODEL,
        temperature=0.5,
        messages=[
            {"role": "system", "content": _system_prompt()},
            {
                "role": "user",
                "content": (
                    "Turn this material into a clean English crypto finding for Telegram. "
                    "Translate any non-English text. Do not reproduce markup or RSS boilerplate. "
                    "Explain why it matters when the source supports a concrete implication. "
                    "For claims about project capabilities, distinguish advertised features from verified behavior. "
                    "Use only the supplied facts and preserve the exact original URL on the final Source line.\n\n"
                    + json.dumps(source_material, ensure_ascii=False)
                ),
            },
        ],
    )
    text = clean_source_text(response.choices[0].message.content or "")
    if not text:
        raise RuntimeError("OpenAI returned an empty finding")
    # Enforce the exact link even if the model omitted or altered it.
    text = text.replace(url, "").strip()
    text = text.removesuffix("Source:").strip()
    return f"{text}\n\nSource: {url}" if text else f"{source_material['source_text']}\n\nSource: {url}"
