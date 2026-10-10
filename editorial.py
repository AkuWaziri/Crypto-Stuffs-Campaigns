"""Groq-powered editorial layer for original, evidence-led crypto findings."""
import json
import os
from functools import lru_cache
from html import unescape
from pathlib import Path

from bs4 import BeautifulSoup
from openai import OpenAI

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
DNA_PATH = Path(__file__).with_name("DNA.md")
BASE_PROMPT = """You are the research analyst and editorial writer for a crypto-native findings feed.
Write in the user's human writing DNA in DNA.md. The DNA controls voice, never facts.

MISSION
Turn source material into an original finding with analysis, not a repost, headline rewrite, generic news summary, or list of links. The reader should learn what happened, what the evidence actually says, what is unusual, and why it matters across crypto: exploits and security, DeFi, NFTs, AI agents, stablecoins/payments, protocols, wallets, infrastructure, developer tools, launches, adoption, on-chain activity, ecosystem progress, and useful builds.

ANALYST METHOD
- Lead with the most specific discovery or signal, not the publisher's headline.
- Extract and connect concrete details: dollar values, token amounts, percentages, user/wallet counts, dates, transaction sequences, fees, TVL, volume, throughput, adoption, before/after comparisons, and implementation details when supplied.
- Explain the mechanism and implication. Make a clear analytical observation about what the evidence suggests, what changed, what looks unusual, who may be affected, or what a builder should investigate.
- Do arithmetic only when inputs are present and the calculation is straightforward; label derived values as estimates/calculations. Never manufacture missing metrics to make a post sound analytical.
- For on-chain or exploit claims, distinguish reported claims from demonstrated evidence. Do not infer wallet ownership, motive, causation, exploit mechanics, or connections unless the supplied material supports them.
- If the source contains a claim without supporting data, say so plainly and explain what would need checking. Do not dress thin material up as a confirmed finding.
- Treat X view counts as engagement metadata, not proof that a claim is true or important.
- Use source text and metadata only. You have not independently opened the URL or verified the underlying data. Do not claim otherwise.
- Do not merely restate a press release. Explain the practical consequence or trade-off in your own words.
- Prefer a compact mini-analysis of 3–6 sentences. Use a natural headline only when it adds clarity; vary structure so the feed does not look templated.
- Use clear natural English; translate non-English text. Preserve exact names, tickers, figures, caveats, and technical terms.
- No generic filler, fake hype, corporate language, forced slang, decorative emojis, HTML/XML, RSS boilerplate, or raw scraped fragments.
- End with exactly one separate line: Source: <the exact original URL>.
Return only the finished Telegram-ready finding."""


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
            "Lead with the surprising, specific finding. Explain the mechanism and numbers, "
            "then make a grounded observation. Use natural crypto-native phrasing. Avoid "
            "generic AI language, forced slang, repetition and unsupported claims."
        )
    return f"{BASE_PROMPT}\n\n--- HUMAN WRITING DNA ---\n{dna}"


@lru_cache(maxsize=1)
def _client():
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GROQ_API_KEY secret is missing")
    return OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")


def write_finding(item):
    """Write an original, evidence-conscious analyst finding and preserve its source URL."""
    url = str(item.get("url") or "").strip()
    if not url:
        raise ValueError("Cannot write a finding without a source URL")

    source_material = {
        "source": item.get("source", "unknown"),
        "author": item.get("author", "unknown"),
        "published_or_seen_at": item.get("created_at", "unknown"),
        "views": item.get("views"),
        "category_or_niche": item.get("niche", ""),
        "tier": item.get("tier", ""),
        "source_text": clean_source_text(item.get("text"))[:9000],
        "original_url": url,
    }
    response = _client().chat.completions.create(
        model=MODEL,
        temperature=0.45,
        messages=[
            {"role": "system", "content": _system_prompt()},
            {
                "role": "user",
                "content": (
                    "Produce an original crypto research finding from this evidence. Analyze the "
                    "specific mechanism, numbers, sequence, change, risk, or builder implication "
                    "that the evidence supports. This must add insight beyond paraphrasing the "
                    "headline/post. If there are no useful numbers, do not invent any: explain "
                    "the concrete technical or ecosystem signal and its limits. Distinguish "
                    "reported claims from verified facts. Do not claim to have opened the source. "
                    "Finish with the exact original URL on one Source line.\n\n"
                    + json.dumps(source_material, ensure_ascii=False)
                ),
            },
        ],
    )
    text = clean_source_text(response.choices[0].message.content or "")
    if not text:
        raise RuntimeError("Groq returned an empty finding")
    # Enforce the exact source URL once, even if the model omitted or altered it.
    text = text.replace(url, "").strip()
    text = text.removesuffix("Source:").strip()
    if not text:
        raise RuntimeError("Groq returned no usable finding text")
    return f"{text}\n\nSource: {url}"
