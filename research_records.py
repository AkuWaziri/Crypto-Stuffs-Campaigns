"""Small persistent audit trail for research candidates and publication decisions."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

RESEARCH_RECORDS_FILE = Path(os.getenv("RESEARCH_RECORDS_FILE", ".research_records.json"))
MAX_RECORDS = max(100, int(os.getenv("RESEARCH_RECORDS_LIMIT", "500")))


def _read_records():
    try:
        data = json.loads(RESEARCH_RECORDS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [record for record in data if isinstance(record, dict)]
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        pass
    return []


def record_candidate(item, status, *, reason=None, draft=None, now=None):
    """Upsert one candidate record while retaining a bounded history.

    Records contain public source metadata and workflow decisions, not API keys
    or private account data. The final draft is optional and only stored when
    generated successfully.
    """
    now = now or datetime.now(timezone.utc)
    timestamp = now.isoformat()
    item_id = str(item.get("id") or item.get("url") or "").strip()
    if not item_id:
        return

    try:
        from research_engine import score_candidate
        triage = score_candidate(item, now=now)
    except Exception:
        triage = {"content_type": "general_finding", "score": None, "dimensions": {}}

    record = {
        "id": item_id,
        "source": str(item.get("source") or "unknown"),
        "url": str(item.get("url") or ""),
        "title_or_snippet": " ".join(str(item.get("text") or "").split())[:600],
        "source_published_at": item.get("created_at"),
        "content_type": triage.get("content_type"),
        "priority_score": triage.get("score"),
        "priority_dimensions": triage.get("dimensions", {}),
        "status": str(status),
        "reason": str(reason)[:500] if reason else None,
        "draft": str(draft)[:1800] if draft else None,
        "updated_at": timestamp,
    }

    records = _read_records()
    records = [old for old in records if str(old.get("id")) != item_id]
    records.append(record)
    records = records[-MAX_RECORDS:]

    RESEARCH_RECORDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = RESEARCH_RECORDS_FILE.with_suffix(RESEARCH_RECORDS_FILE.suffix + ".tmp")
    temporary.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, RESEARCH_RECORDS_FILE)


def load_research_records():
    """Return the bounded research audit trail for tests and diagnostics."""
    return _read_records()
