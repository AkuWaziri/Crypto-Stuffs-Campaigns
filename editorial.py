"""Groq-powered research and editorial gate for original crypto findings."""
import json
import os
from functools import lru_cache
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from openai import OpenAI

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
DNA_PATH = Path(__file__).with_name("DNA.md")
SKIP_MARKER = "SKIP_ITEM"
ARTICLE_TIMEOUT_SECONDS = 8
ARTICLE_TEXT_LIMIT = 12000

BASE_PROMPT = """You are the research editor, source investigator, and crypto-native analyst for a high-signal findings feed. Your job is to FIND the actual story, not make every candidate sound interesting.

EDITORIAL GATE — APPLY THIS BEFORE WRITING
Reject a candidate by returning exactly SKIP_ITEM when, after reading the supplied source material:
- it is only a vague prediction, opinion, listicle, promotional claim, or recycled headline;
- it gives no concrete event, technical mechanism, data point, implementation detail, primary-source lead, or genuinely useful explanation;
- its crypto connection is forced or merely hypothetical;
- the only possible analysis is saying that the source lacks evidence.
Do not rescue weak content with polished speculation. A smaller feed of real discoveries is better than a full feed of filler.

WHAT QUALIFIES
Prioritize specific crypto discoveries across exploits/security, on-chain wallet or fund movements, DeFi mechanics, stablecoins/payments, protocol changes, AI agents, NFTs, infrastructure, developer tools, launches, governance, adoption, and unusual market or ecosystem behavior. Strong leads include transaction hashes, wallet addresses, measurable changes, code/PRs, postmortems, technical docs, benchmarks, specific rollout details, reproducible demos, and first-hand builder reports. A useful technical explanation can qualify without numbers if it contains real mechanism-level detail.

RESEARCH AND EVIDENCE RULES
- Use the supplied full-page text when available, not just its headline or RSS snippet.
- Find the most specific new fact. Explain the mechanism, sequence, contradiction, consequence, or practical builder insight.
- Never invent metrics, wallet links, causality, motives, security findings, or facts not in the material.
- Do not imply you independently verified a URL, transaction, benchmark, or allegation. Treat unverified claims as claims.
- Do not infer a broad market trend from one article. Do not attach generic staking, yield, AI, or DeFi implications unless the evidence connects them.
- If the source is thin but points to a concrete lead, only publish if that lead itself is specific and useful. Otherwise return SKIP_ITEM.
- Do not turn every item into a warning that data is missing. If there is no finding, skip it.

WRITING STYLE
Follow the user's human writing DNA in DNA.md. Lead with the finding, not a generic intro. Make it feel observed and investigative: specific detail → how it works / what changed → why the detail is surprising or useful. Use natural crypto-native English, concise and varied. Usually 2–5 sentences. Avoid generic AI/corporate language, fake hype, repetitive templates, forced slang, decorative emojis, HTML, and RSS boilerplate. A short headline is fine when useful, but vary structure.
Return only the finished Telegram-ready finding, or exactly SKIP_ITEM if it fails the editorial gate.
The finished finding must end with exactly one separate line: Source: <the exact original URL>."""

def clean_source_text(value):
    """Strip HTML/XML markup and decode entities before editorial generation."""
    raw = unescape(str(value or ""))
    soup = BeautifulSoup(raw, "html.parser")
    for node in soup(["script", "style", "noscript", "svg"]):
        node.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def _fetch_article_text(url):
    """Fetch readable publisher text so RSS titles/snippets are not the only evidence."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return ""
        if parsed.hostname.lower() in {"localhost", "127.0.0.1", "::1"}:
            return ""
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; CryptoStuffsResearch/1.0)",
                "Accept": "text/html,application/xhtml+xml",
            },
            timeout=ARTICLE_TIMEOUT_SECONDS,
            allow_redirects=True,
        )
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        if "html" not in content_type:
            return ""
        soup = BeautifulSoup(response.text, "html.parser")
        for node in soup(["script", "style", "noscript", "nav", "footer", "header", "svg", "form"]):
            node.decompose()

        candidates = []
        for selector in (
            "article",
            '[itemprop="articleBody"]',
            "main",
            ".article-content",
            ".post-content",
            ".postArticle-content",
            ".entry-content",
        ):
            for node in soup.select(selector):
                text = clean_source_text(str(node))
                if len(text) > len(" ".join(candidates)):
                    candidates.append(text)
        if not candidates:
            body = soup.body or soup
            candidates.append(clean_source_text(str(body)))

        text = max(candidates, key=len, default="")
        # A short page title/consent screen is not useful additional evidence.
        return text[:ARTICLE_TEXT_LIMIT] if len(text) >= 500 else ""
    except Exception as exc:
        print(f"article_fetch_skipped={url}: {type(exc).__name__}")
        return ""


@lru_cache(maxsize=1)
def _system_prompt():
    """Load editable human writing DNA with a safe fallback."""
    try:
        dna = DNA_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        dna = (
            "Lead with a specific discovery. Explain the mechanism and concrete details, "
            "then make a grounded observation. Avoid generic AI language, speculation, "
            "repetition, and unsupported claims."
        )
    return f"{BASE_PROMPT}\n\n--- HUMAN WRITING DNA ---\n{dna}"


@lru_cache(maxsize=1)
def _client():
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GROQ_API_KEY secret is missing")
    return OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")


def write_finding(item):
    """Investigate the linked page, reject weak leads, and write evidence-led findings.

    Returns None when the item does not pass the editorial gate.
    """
    url = str(item.get("url") or "").strip()
    if not url:
        raise ValueError("Cannot write a finding without a source URL")

    source_text = clean_source_text(item.get("text"))
    article_text = _fetch_article_text(url)
    is_skill_lane = item.get("content_lane") == "skill_showcase"
    is_howto_lane = item.get("content_lane") == "research_guides"
    source_material = {
        "content_lane": item.get("content_lane", "crypto_findings"),
        "skill_profile": item.get("skill_profile", ""),
        "source": item.get("source", "unknown"),
        "author": item.get("author", "unknown"),
        "published_or_seen_at": item.get("created_at", "unknown"),
        "views": item.get("views"),
        "category_or_niche": item.get("niche", ""),
        "tier": item.get("tier", ""),
        "feed_snippet_or_post": source_text[:6000],
        "fetched_article_text": article_text,
        "original_url": url,
    }
    if is_howto_lane:
        task_prompt = (
            "Turn this source into a genuinely useful, step-by-step how-to guide for a reader who wants "
            "to reproduce the workflow at little or no cost. Topic can include DeFi, crypto security "
            "and incident response, mining education, AI/API credits, X tools, VPS/cloud setup, "
            "trading mechanics, wallet safety, on-chain research, free developer tooling, or related "
            "practical topics. Start by checking the supplied article/page and prefer official product "
            "docs, primary sources, and the actual tool URL over summaries. Explain prerequisites, "
            "ordered steps, the free tier/credit conditions if stated, limitations, and a simple way "
            "to verify success. Keep every claim about pricing, eligibility, limits, rewards, or free "
            "availability tied to the source; these terms change. Do not invent steps or imply a paid "
            "feature is free. If the source does not support a reproducible guide, return exactly "
            "SKIP_ITEM. For trading, mining, and DeFi, distinguish educational steps from a profit "
            "promise and state material risks without giving unsupported token picks. For security, "
            "keep actions defensive or explicitly authorized. Use concise numbered steps where useful, "
            "make the guide clear enough to follow, and include direct links supplied by the source "
            "when relevant. Finish with the exact original reference URL on a separate line: "
            "Source: <URL>.\n\n"
        )
    elif is_skill_lane:
        task_prompt = (
            "You are a professional content strategist helping the owner publish original public "
            "posts that demonstrate practical thinking across these skill lenses: motion video "
            "creator for Web3 protocols; Web3 compliance analysis; ethical bug-bounty and smart-contract "
            "security research; referral/points campaign design; and protocol reputation/community "
            "management. The skill profile for this source is "
            + str(item.get("skill_profile") or "best fit") + ".\n\n"
            "Research the supplied article/page and turn its concrete details into a useful, "
            "publish-ready post in the owner's own editorial voice. Do not merely summarize it. "
            "Choose a credible angle such as a motion-video concept that explains a real protocol "
            "mechanism; a compliance risk/control checklist grounded in official guidance; a "
            "defensive bug-bounty hypothesis or scope question; a points/referral campaign mechanic "
            "with anti-Sybil and measurable incentive design; or a reputation strategy tied to real "
            "contributor/governance behavior. Include a specific observation and a suggested post "
            "or practical framework the owner could publish. Make it feel personal and original, "
            "not like a job advert or generic list of services.\n"
            "Never invent that the owner audited, built, advised, represented, or worked for a "
            "project. Do not claim professional qualifications or legal authority. For compliance, "
            "explain issues as general research, not legal advice. For bug bounty, keep guidance "
            "authorized, defensive, and within a program's scope. Never fabricate metrics, quotes, "
            "product behavior, project commitments, or a personal case study. If the source has no "
            "substantive detail that can support a useful skill-led post, return exactly SKIP_ITEM. "
            "Prefer official docs, whitepapers, research, technical blogs and primary sources. "
            "Distinguish source facts from your suggested idea. Keep it concise and specific, normally "
            "3–6 sentences. End with the exact original URL on a separate line: Source: <URL>.\n\n"
        )
    else:
        task_prompt = (
            "Act as a selective crypto researcher and editor. First decide whether this contains "
            "a real, specific finding worth a crypto-native reader's attention. Use the full page "
            "text if available. Do not force a crypto angle. If it is generic speculation, marketing, "
            "a thin listicle, or only supports commentary about missing evidence, return exactly "
            "SKIP_ITEM. Otherwise write the most specific evidence-backed finding and explain its "
            "mechanism or practical significance. Preserve uncertainty; do not pretend you "
            "independently verified the page or any on-chain claim. End with the exact original URL "
            "on one Source line.\n\n"
        )

    response = _client().chat.completions.create(
        model=MODEL,
        temperature=0.35,
        messages=[
            {"role": "system", "content": _system_prompt()},
            {
                "role": "user",
                "content": task_prompt + json.dumps(source_material, ensure_ascii=False),
            },
        ],
    )
    text = clean_source_text(response.choices[0].message.content or "")
    if not text:
        raise RuntimeError("Groq returned an empty finding")
    if text.strip().upper() == SKIP_MARKER or text.strip().upper().startswith(SKIP_MARKER + " "):
        return None

    # Enforce the exact original URL once, even if the model omitted or altered it.
    text = text.replace(url, "").strip()
    text = text.removesuffix("Source:").strip()
    if not text or text.strip().upper() == SKIP_MARKER:
        return None
    return f"{text}\n\nSource: {url}"
