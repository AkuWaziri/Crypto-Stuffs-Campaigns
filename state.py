import json
from pathlib import Path

PATH = Path(".campaign_state.json")

def load_seen():
    if not PATH.exists():
        return set()
    try:
        data = json.loads(PATH.read_text())
        return set(data.get("seen", []))
    except Exception:
        return set()

def save_seen(seen):
    values = list(seen)[-5000:]
    PATH.write_text(json.dumps({"seen": values}, indent=2))
