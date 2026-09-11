from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from models import FreshSignal

STORE_PATH = Path("data/signals.jsonl")


def append_signal(signal: FreshSignal) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(signal)
    payload["source"] = asdict(signal.source)
    payload["published_at"] = signal.published_at.astimezone(timezone.utc).isoformat()
    with STORE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, separators=(",", ":")) + "\n")


def recent_signals(limit: int = 100) -> list[dict]:
    if limit < 1 or not STORE_PATH.exists():
        return []
    with STORE_PATH.open("r", encoding="utf-8") as handle:
        rows = handle.readlines()[-limit:]
    return [json.loads(row) for row in rows]
