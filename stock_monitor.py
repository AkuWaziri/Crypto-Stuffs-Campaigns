from datetime import datetime, timezone
from typing import Any

from models import ActivityEvent


def parse_13f_position(row: dict[str, Any], *, source: str = "sec_13f") -> ActivityEvent | None:
    """Normalize a public institutional holding change.

    13F data is disclosure data, not an exact execution feed. The event therefore
    uses BUY/SELL only when the supplied normalized record explicitly identifies
    the direction; otherwise UNKNOWN is used.
    """
    entity = row.get("entity") or row.get("manager") or row.get("institution")
    asset = row.get("asset") or row.get("cusip") or row.get("ticker")
    if not entity or not asset:
        return None

    direction = str(row.get("action") or row.get("direction") or "UNKNOWN").upper()
    if direction not in {"BUY", "SELL", "UNKNOWN"}:
        direction = "UNKNOWN"

    timestamp = row.get("timestamp")
    if isinstance(timestamp, (int, float)):
        when = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    else:
        when = datetime.now(timezone.utc)

    evidence = tuple(row.get("evidence") or ())
    reference = row.get("accession") or row.get("reference")
    return ActivityEvent(
        entity=str(entity),
        entity_type=str(row.get("entity_type") or "INSTITUTION"),
        asset=str(asset),
        action=direction,
        value_usd=float(row["value_usd"]) if row.get("value_usd") is not None else None,
        chain="public-disclosure",
        timestamp=when,
        source=source,
        tx_or_reference=str(reference) if reference else None,
        evidence=evidence,
    )
