import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
X_AUTH_TOKEN = os.getenv("X_AUTH_TOKEN", "")
X_CT0 = os.getenv("X_CT0", "")
X_SEARCH_LIMIT = int(os.getenv("X_SEARCH_LIMIT", "30"))
MAX_FEED_ITEMS = int(os.getenv("MAX_FEED_ITEMS", "10"))
LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", "36"))
ENABLE_WEB_SOURCES = os.getenv("ENABLE_WEB_SOURCES", "true").lower() == "true"
USER_AGENT = os.getenv("USER_AGENT", "Crypto-Stuffs-Campaigns/1.0")
X_SEARCH_QUERY_ID = os.getenv("X_SEARCH_QUERY_ID", "")
