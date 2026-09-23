from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from config import USER_AGENT

SOURCES = [
    ("zealy", "https://www.zealy.io/earn"),
    ("galxe", "https://app.galxe.com/quest"),
    ("layer3", "https://layer3.xyz/"),
]

def fetch_public_campaigns():
    items = []
    for source, url in SOURCES:
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            text = " ".join(soup.stripped_strings)
            items.append({"id": f"web:{source}", "author": source, "text": text[:12000], "url": url, "created_at": datetime.now(timezone.utc).isoformat(), "source": source})
        except Exception as exc:
            print(f"web_source_error={source}: {exc}")
    return items
