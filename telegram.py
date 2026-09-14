import os

import requests


def send_message(text: str, *, token: str | None = None, chat_id: str | None = None, dry_run: bool = False) -> bool:
    token = token or os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
    if dry_run or not token or not chat_id:
        print(text)
        return False
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=20,
    )
    response.raise_for_status()
    return bool(response.json().get("ok"))
