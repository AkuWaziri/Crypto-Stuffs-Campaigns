"""Groq-powered research and editorial gate for original crypto findings."""
import json
import re
import os
import time
from functools import lru_cache
from html import unescape
from pathlib import Path
from urllib.parse import parse_qs, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from openai import OpenAI

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
DNA_PATH = Path(__file__).with_name("DNA.md")
SKIP_MARKER = "SKIP_ITEM"
ARTICLE_TIMEOUT_SECONDS = 8
ARTICLE_TEXT_LIMIT = 2000
MAX_GROQ_RETRY_WAIT_SECONDS = 30
GROQ_RATE_LIMIT_RETRIES = 2
SOCIAL_SNIPPET_LIMIT = 1000
GROQ_DAILY_QUOTA_EXHAUSTED = False


class GroqQuotaExhaustedError(RuntimeError):
    """Raised when Groq daily token quota is exhausted for this run."""

BASE_PROMPT = """You are the selective research editor for a high-signal crypto findings feed.

GATE
Return exactly SKIP_ITEM only when the source is irrelevant, purely promotional, generic speculation, or contains no identifiable claim, event, tool, project, mechanism, or useful question. Do not require every item to contain a metric, transaction hash, or full article. A named project plus a specific launch, change, incident, tool, implementation, or first-hand observation is enough to report cautiously. Never reject a short social post only because it is short. When evidence is limited to a headline/snippet or an unverified social claim, explicitly attribute it to the source and explain only what the supplied text supports.

WHAT QUALIFIES
Prioritize concrete discoveries about exploits/security, on-chain activity, DeFi, stablecoins/payments, protocol changes, AI agents, NFTs, infrastructure, developer tools, launches, governance, adoption, and unusual ecosystem behavior. Useful evidence includes transaction hashes, addresses, measurable changes, code/PRs, postmortems, technical docs, benchmarks, rollout details, reproducible demos, and first-hand builder reports.

EVIDENCE
Use supplied page text when available. Identify the specific new fact and explain its mechanism, sequence, consequence, or practical value. Never invent metrics, links, causality, motives, security findings, or facts. Do not claim independent verification. Treat unverified claims as claims. Do not infer broad trends from one source. For social posts, preserve uncertainty and explain only what the post supports; skip generic hype.

STYLE
Follow the user's human writing DNA in DNA.md. Lead with the finding; write natural, concise, varied crypto-native English, usually 2–5 sentences. Avoid generic AI/corporate language, fake hype, forced slang, repeated templates, decorative emojis, HTML, and RSS boilerplate. How-to guides must contain reproducible steps supported by the source; do not invent pricing, eligibility, rewards, or free-tier terms. Skill-led posts must not invent the user's credentials or experience. Security guidance must be defensive or authorized.

Return only a Telegram-ready finding or exactly SKIP_ITEM. End every finding with one separate line: Source: <the exact original URL>."""


def _direct_source_url(url):
    """Unwrap common news/search tracking links when they expose the publisher URL."""
    raw = str(url or "").strip()
    try:
        parsed = urlparse(raw)
        host = (parsed.hostname or "").lower()
        query = parse_qs(parsed.query)
        if host.endswith("bing.com") and parsed.path.startswith("/news/apiclick.aspx"):
            for key in ("url", "u", "target"):
                for candidate in query.get(key, []):
                    candidate = unescape(candidate).strip()
                    target = urlparse(candidate)
                    if target.scheme in {"http", "https"} and target.hostname:
                        return _direct_source_url(candidate)
        if parsed.scheme in {"http", "https"} and parsed.hostname:
            tracking = {"fbclid", "gclid", "mc_cid", "mc_eid", "ref_src", "ref_url"}
            kept = []
            for part in parsed.query.split("&") if parsed.query else []:
                key = part.split("=", 1)[0].lower()
                if key not in tracking and not key.startswith("utm_"):
                    kept.append(part)
            return urlunparse(parsed._replace(query="&".join(kept), fragment=""))
    except Exception:
        pass
    return raw


def _validate_generated_finding(value, source_url):
    """Reject broken/truncated, bloated, or source-dump outputs before delivery."""
    raw = unescape(str(value or ""))
    # Remove the model's source dump before HTML cleanup collapses line breaks.
    raw = re.split(
        r"(?im)^\s*(?:SOURCES|REFERENCES|Source:.*|Sources:.*|References:.*)\s*$",
        raw,
        maxsplit=1,
    )[0]
    text = clean_source_text(raw)
    if not text or text.strip().upper().startswith(SKIP_MARKER):
        return None

    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(("source:", "sources:", "references:")):
            break
        if stripped.upper() in {"SOURCES", "REFERENCES"}:
            break
        kept.append(line)
    body = " ".join(" ".join(kept).split()).strip(" \t\r\n-")
    if not body:
        return None
    if len(body) > 1800:
        print(f"editorial_output_rejected=too_long chars={len(body)}")
        return None
    if body.count("http://") + body.count("https://") > 2:
        print("editorial_output_rejected=multiple_embedded_links")
        return None
    if "**" in body or "###" in body:
        print("editorial_output_rejected=formatted_report")
        return None
    if body[-1:] not in ".!?”’\\\"')]}":
        print("editorial_output_rejected=incomplete_ending")
        return None
    last_words = body.rstrip(".!?”’\\\"')]}").lower().split()
    if last_words and last_words[-1] in {
        "a", "an", "and", "are", "as", "at", "because", "but", "by", "for",
        "from", "if", "in", "into", "is", "of", "on", "or", "that", "the",
        "to", "was", "were", "with", "without", "while",
    }:
        print("editorial_output_rejected=dangling_last_word")
        return None
    return f"{body}\n\nSource: {source_url}"


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
    global GROQ_DAILY_QUOTA_EXHAUSTED
    if GROQ_DAILY_QUOTA_EXHAUSTED:
        print("groq_daily_quota_exhausted_skip=1")
        return None
    url = str(item.get("url") or "").strip()
    if not url:
        raise ValueError("Cannot write a finding without a source URL")

    source_text = clean_source_text(item.get("text"))
    source_kind = str(item.get("source") or "").lower()
    # Social posts are the primary evidence already; fetching each status URL
    # adds latency and often returns an inaccessible shell instead of useful text.
    social_sources = {"x", "x_social", "x_high_performance", "reddit", "telegram", "bluesky", "farcaster"}
    article_text = "" if source_kind in social_sources else _fetch_article_text(url)
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
        "feed_snippet_or_post": source_text[:SOCIAL_SNIPPET_LIMIT],
        "fetched_article_text": article_text[:ARTICLE_TEXT_LIMIT],
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

    # Reject only clearly empty/generic material before spending a Groq call.
    # Specific short social posts remain eligible for the model's evidence gate.
    combined_source = f"{source_text} {article_text}".strip()
    specificity_markers = (
        "0x", "tx hash", "transaction", "github.com", "pull request", "postmortem",
        "exploit", "vulnerability", "launched", "deploy", "upgrade", "proposal",
        "benchmark", "million", "billion", "%", "api", "docs", "how to", "step",
        "wallet", "contract", "mainnet", "testnet", "open source", "release",
    )
    generic_markers = (
        "you won't believe", "huge news", "this is bullish", "game changer",
        "mass adoption is coming", "the future of crypto", "don't miss out",
    )
    lower_source = combined_source.lower()
    if not combined_source or (
        any(marker in lower_source for marker in generic_markers)
        and not any(marker in lower_source for marker in specificity_markers)
    ):
        print(f"cheap_editorial_skip={url}: thin_or_generic_source")
        return None

    # Keep generated output and GPT-OSS reasoning bounded. Guides get more
    # room than ordinary findings, but all calls have an explicit ceiling.
    if is_howto_lane:
        output_token_limit = 400
    elif is_skill_lane:
        output_token_limit = 300
    else:
        output_token_limit = 300

    request = {
        "model": MODEL,
        "temperature": 0.35,
        "max_completion_tokens": output_token_limit,
        "reasoning_effort": "low",
        "messages": [
            {"role": "system", "content": _system_prompt()},
            {
                "role": "user",
                "content": task_prompt + json.dumps(source_material, ensure_ascii=False),
            },
        ],
    }
    client = _client()
    response = None
    # Groq's free/on-demand token limits can return transient 429s during a
    # multi-item run. Retry instead of silently losing that candidate.
    for attempt in range(GROQ_RATE_LIMIT_RETRIES):
        try:
            response = client.chat.completions.create(**request)
            break
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if status is None:
                status = getattr(getattr(exc, "response", None), "status_code", None)
            error_text = str(exc).lower()
            if status == 429 and (
                "tokens per day" in error_text
                or ("rate_limit_exceeded" in error_text and "token" in error_text)
            ):
                GROQ_DAILY_QUOTA_EXHAUSTED = True
                print("groq_daily_quota_exhausted=1; stopping editorial calls for this run")
                raise GroqQuotaExhaustedError("Groq daily token quota exhausted; stopped further editorial calls") from exc
            if status != 429 or attempt == GROQ_RATE_LIMIT_RETRIES - 1:
                raise
            wait_seconds = min(2 ** (attempt + 1), MAX_GROQ_RETRY_WAIT_SECONDS)
            headers = getattr(getattr(exc, "response", None), "headers", {}) or {}
            retry_after = headers.get("retry-after")
            try:
                wait_seconds = min(MAX_GROQ_RETRY_WAIT_SECONDS, max(wait_seconds, float(retry_after)))
            except (TypeError, ValueError):
                pass
            print(f"groq_rate_limited_retry={attempt + 1} wait_seconds={wait_seconds}")
            time.sleep(wait_seconds)
    if response is None:
        raise RuntimeError("Groq did not return a response after rate-limit retries")
    text = clean_source_text(response.choices[0].message.content or "")
    if not text:
        raise RuntimeError("Groq returned an empty finding")
    if text.strip().upper() == SKIP_MARKER or text.strip().upper().startswith(SKIP_MARKER + " "):
        return None

    # Validate the generated body before delivery, then append one clean direct source link.
    return _validate_generated_finding(text, url)
