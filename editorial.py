"""Evidence-preserving, human-tone rewrites for the Telegram findings feed."""
import json
import os
from typing import Any

import requests

DEFAULT_MODEL = "gpt-4o-mini"
MAX_INPUT_CHARS = 2200


def _clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def _story_id(item: dict) -> str:
    return str(item.get("id") or item.get("url") or "")


def _fallback(item: dict) -> str:
    return _clean(item.get("text"))[:900]


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Model response did not contain a JSON object")
    return json.loads(text[start:end + 1])


def _prompt(items: list[dict]) -> str:
    evidence = []
    for item in items:
        evidence.append({
            "id": _story_id(item),
            "source": _clean(item.get("source")),
            "author": _clean(item.get("author")),
            "published_at": _clean(item.get("created_at")),
            "title": _clean(item.get("title")),
            "evidence": _clean(item.get("text"))[:MAX_INPUT_CHARS],
            "url": _clean(item.get("url")),
        })
    return (
        "Turn each supplied crypto source into one concise, finished finding for a private Telegram feed. "
        "Return ONLY valid JSON shaped like {\"items\":[{\"id\":\"source id\",\"story\":\"finished finding\"}]}. "
        "Write like a knowledgeable crypto-native person who found something interesting, checked the details, "
        "and wants to tell another person. Preserve useful specifics: numbers, dates, actors, wallet behavior, "
        "technical details, and contradictions. Lead with the most interesting finding. Explain the sequence "
        "in plain language and why it matters. Natural contractions and dry humor or sarcasm are fine when earned; "
        "vary the voice to fit the evidence. Use paragraphs, not bullet lists. Do not add generic introductions, "
        "headings, engagement bait, calls to action, recommendations, or phrases like 'this is a game changer'. "
        "Do not invent facts, motives, wallet attribution, causation, quotes, numbers, or context missing from the "
        "evidence. Treat allegations as allegations. If a source lacks enough substance to support a useful finding, "
        "return an empty story for it. Do not merely copy a news headline: synthesize the provided evidence into a "
        "readable finding. Aim for 60-140 words when evidence supports it; shorter is fine when it doesn't. "
        "The source link is appended separately. Use each input id exactly once and never merge unrelated sources.\n\n"
        + json.dumps({"items": evidence}, ensure_ascii=False)
    )


def write_findings(items: list[dict]) -> dict[str, str]:
    """Return source-id -> authored finding; fall back safely if no model is configured."""
    if not items:
        return {}
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("editorial_mode=source_text_fallback (OPENAI_API_KEY not configured)")
        return {_story_id(item): _fallback(item) for item in items if _fallback(item)}

    base_url = (os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
                or "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a careful crypto researcher and natural, human-sounding writer. Evidence first. Never fabricate."},
            {"role": "user", "content": _prompt(items)},
        ],
        "temperature": 0.65,
        "response_format": {"type": "json_object"},
    }
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=90,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = _extract_json(content)
        valid_ids = {_story_id(item) for item in items}
        output = {}
        for entry in parsed.get("items", []):
            item_id = str(entry.get("id") or "")
            story = _clean(entry.get("story"))
            if item_id in valid_ids and story:
                output[item_id] = story[:1600]
        print(f"editorial_mode=model:{model} rewritten={len(output)}")
        for item in items:
            item_id = _story_id(item)
            if item_id not in output and _fallback(item):
                output[item_id] = _fallback(item)
        return output
    except Exception as exc:
        print(f"editorial_error={exc}; using source text")
        return {_story_id(item): _fallback(item) for item in items if _fallback(item)}
