from __future__ import annotations

import re
from dataclasses import dataclass

from models import Narrative


@dataclass(frozen=True)
class TokenConcept:
    narrative_id: str
    name: str
    symbol: str
    thesis: str
    source_signal_ids: tuple[str, ...]


def _words(text: str) -> list[str]:
    return [word.upper() for word in re.findall(r"[A-Za-z0-9]{3,}", text)]


def _symbol(narrative: Narrative) -> str:
    for signal in narrative.signals:
        match = re.search(r"\$([A-Za-z][A-Za-z0-9]{1,9})", signal.text)
        if match:
            return match.group(1).upper()
    words = _words(narrative.title)
    return "".join(words[:3])[:10] or "TREND"


def build_concept(narrative: Narrative) -> TokenConcept:
    words = _words(narrative.title)
    symbol = _symbol(narrative)
    name = " ".join(word.title() for word in words[:4]) or "Emerging Trend"
    thesis = (
        f"Concept derived from the emerging narrative: {narrative.title}. "
        "This is a research concept only and is not a recommendation or execution instruction."
    )
    return TokenConcept(
        narrative_id=narrative.narrative_id,
        name=name,
        symbol=symbol,
        thesis=thesis,
        source_signal_ids=tuple(signal.signal_id for signal in narrative.signals),
    )
