import json
from pathlib import Path

STATE_PATH = Path(".whalesboarder_state.json")
MAX_KEYS = 2000


def load_seen_keys() -> set[str]:
    if not STATE_PATH.exists():
        return set()
    try:
        payload = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        keys = payload.get("seen_keys", [])
        return {str(key) for key in keys}
    except (OSError, ValueError, AttributeError):
        return set()


def remember_keys(keys: set[str]) -> None:
    existing = load_seen_keys()
    combined = list(existing | keys)
    if len(combined) > MAX_KEYS:
        combined = combined[-MAX_KEYS:]
    STATE_PATH.write_text(
        json.dumps({"seen_keys": combined}, indent=2),
        encoding="utf-8",
    )
