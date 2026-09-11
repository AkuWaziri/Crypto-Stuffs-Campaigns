from __future__ import annotations

import json
import os
from typing import Any, Callable
from urllib.request import Request, urlopen

from intelligence_models import IntelligenceAssessment
from models import Narrative


DEFAULT_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b"


class LLMIntelligenceProvider:
    """OpenAI-compatible intelligence provider. It has no execution access."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_url: str | None = None,
        model: str | None = None,
        request_fn: Callable[[Request], Any] | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("INTELLIGENCE_API_KEY", "")
        self.api_url = api_url or os.getenv("INTELLIGENCE_API_URL", DEFAULT_URL)
        self.model = model or os.getenv("INTELLIGENCE_MODEL", DEFAULT_MODEL)
        self._request_fn = request_fn or urlopen

    def assess(self, narrative: Narrative) -> IntelligenceAssessment:
        if not self.api_key:
            raise RuntimeError("INTELLIGENCE_API_KEY is not configured")

        payload = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": self._narrative_payload(narrative)},
            ],
        }
        request = Request(
            self.api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with self._request_fn(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
        return self._parse_assessment(narrative, body)

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are a crypto trend intelligence analyst. Interpret evidence only. "
            "Do not trade, buy, sell, launch tokens, or recommend execution. "
            "Return JSON only with: event_summary, canonical_topic, narrative, "
            "novelty, momentum, cultural_resonance, crypto_relevance, tokenability, "
            "contradiction, confidence, reasons. Scores are 0-100. "
            "Be conservative when evidence is weak or contradictory."
        )

    @staticmethod
    def _narrative_payload(narrative: Narrative) -> str:
        evidence = [
            {
                "source": signal.source.handle,
                "text": signal.text,
                "url": signal.url,
                "published_at": signal.published_at.isoformat(),
            }
            for signal in narrative.signals
        ]
        return json.dumps(
            {
                "title": narrative.title,
                "signals": evidence,
                "deterministic_scores": {
                    "novelty": narrative.novelty_score,
                    "meme_potential": narrative.meme_potential_score,
                    "crypto_relevance": narrative.crypto_relevance_score,
                    "velocity": narrative.velocity_score,
                },
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _parse_assessment(narrative: Narrative, body: dict[str, Any]) -> IntelligenceAssessment:
        try:
            content = body["choices"][0]["message"]["content"]
            data = json.loads(content) if isinstance(content, str) else content
            fields = {
                "event_summary": str(data["event_summary"]),
                "canonical_topic": str(data["canonical_topic"]),
                "narrative": str(data["narrative"]),
                "novelty": float(data["novelty"]),
                "momentum": float(data["momentum"]),
                "cultural_resonance": float(data["cultural_resonance"]),
                "crypto_relevance": float(data["crypto_relevance"]),
                "tokenability": float(data["tokenability"]),
                "contradiction": float(data["contradiction"]),
                "confidence": float(data["confidence"]),
                "reasons": tuple(str(item) for item in data["reasons"]),
            }
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("invalid intelligence response") from exc

        numeric = (
            fields["novelty"], fields["momentum"], fields["cultural_resonance"],
            fields["crypto_relevance"], fields["tokenability"],
            fields["contradiction"], fields["confidence"],
        )
        if any(value < 0 or value > 100 for value in numeric):
            raise ValueError("intelligence score outside 0-100")
        if not fields["reasons"]:
            raise ValueError("intelligence response has no reasons")

        return IntelligenceAssessment(narrative_id=narrative.narrative_id, **fields)
