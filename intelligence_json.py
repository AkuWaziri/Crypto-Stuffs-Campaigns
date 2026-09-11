from __future__ import annotations

import json
from typing import Any

from intelligence_models import IntelligenceAssessment
from models import Narrative


REQUIRED_FIELDS = {
    "event_summary",
    "canonical_topic",
    "narrative",
    "novelty",
    "momentum",
    "cultural_resonance",
    "crypto_relevance",
    "tokenability",
    "contradiction",
    "confidence",
    "reasons",
}


def parse_assessment(text: str, narrative: Narrative) -> IntelligenceAssessment:
    """Parse one strict JSON assessment. Invalid model output fails closed."""
    try:
        payload: Any = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("intelligence response is not valid JSON") from exc

    if not isinstance(payload, dict) or not REQUIRED_FIELDS.issubset(payload):
        raise ValueError("intelligence response is missing required fields")

    numeric_fields = (
        "novelty",
        "momentum",
        "cultural_resonance",
        "crypto_relevance",
        "tokenability",
        "contradiction",
        "confidence",
    )
    values: dict[str, float] = {}
    for field in numeric_fields:
        value = payload[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be numeric")
        if not 0.0 <= float(value) <= 100.0:
            raise ValueError(f"{field} must be between 0 and 100")
        values[field] = float(value)

    reasons = payload["reasons"]
    if not isinstance(reasons, list) or not all(isinstance(item, str) for item in reasons):
        raise ValueError("reasons must be a list of strings")

    text_fields = ("event_summary", "canonical_topic", "narrative")
    if not all(isinstance(payload[field], str) and payload[field].strip() for field in text_fields):
        raise ValueError("text fields must be non-empty strings")

    return IntelligenceAssessment(
        narrative_id=narrative.narrative_id,
        event_summary=payload["event_summary"].strip(),
        canonical_topic=payload["canonical_topic"].strip(),
        narrative=payload["narrative"].strip(),
        reasons=tuple(reasons),
        **values,
    )
