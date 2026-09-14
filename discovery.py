from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WhaleCandidate:
    wallet: str
    label: str | None
    entity_type: str
    source: str
    roi_pct: float | None = None
    win_rate_pct: float | None = None
    evidence: tuple[str, ...] = ()


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def parse_trader_candidates(payload: Any, source: str = "provider") -> list[WhaleCandidate]:
    """Normalize leaderboard/trader responses into WhaleCandidate objects.

    The provider response is deliberately treated as untrusted input. Missing
    performance fields remain unknown rather than being inferred.
    """
    if isinstance(payload, dict):
        rows = payload.get("traders") or payload.get("data") or payload.get("results") or []
    else:
        rows = payload
    if not isinstance(rows, list):
        return []

    candidates: list[WhaleCandidate] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        wallet = row.get("wallet") or row.get("address") or row.get("user_address")
        if not wallet:
            continue
        roi = _number(row.get("roi") or row.get("roiPct") or row.get("roi_pct"))
        win_rate = _number(row.get("winRate") or row.get("win_rate") or row.get("win_rate_pct"))
        label = row.get("name") or row.get("label")
        entity_type = row.get("entityType") or row.get("type") or "WHALE_WALLET"
        candidates.append(
            WhaleCandidate(
                wallet=str(wallet),
                label=str(label) if label else None,
                entity_type=str(entity_type),
                source=source,
                roi_pct=roi,
                win_rate_pct=win_rate,
            )
        )
    return candidates


def select_smart_money(
    candidates: list[WhaleCandidate],
    *,
    min_roi_pct: float = 50.0,
    min_win_rate_pct: float | None = None,
) -> list[WhaleCandidate]:
    """Select proven performers without calling every large wallet smart money."""
    selected = []
    for candidate in candidates:
        if candidate.roi_pct is None or candidate.roi_pct < min_roi_pct:
            continue
        if min_win_rate_pct is not None and (
            candidate.win_rate_pct is None or candidate.win_rate_pct < min_win_rate_pct
        ):
            continue
        selected.append(candidate)
    return selected
