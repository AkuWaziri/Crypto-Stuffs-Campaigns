import os

def _csv(name, default=""):
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
X_AUTH_TOKEN = os.getenv("X_AUTH_TOKEN", "")
X_CT0 = os.getenv("X_CT0", "")
X_SEARCH_LIMIT = int(os.getenv("X_SEARCH_LIMIT", "30"))
MAX_FEED_ITEMS = int(os.getenv("MAX_FEED_ITEMS", "10"))
LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", "36"))
ENABLE_WEB_SOURCES = os.getenv("ENABLE_WEB_SOURCES", "true").lower() == "true"
USER_AGENT = os.getenv("USER_AGENT", "Crypto-Stuffs-Campaigns/2.0")
X_SEARCH_QUERY_ID = os.getenv("X_SEARCH_QUERY_ID", "")

REDDIT_SUBREDDITS = _csv(
    "REDDIT_SUBREDDITS",
    "CryptoCurrency,Bitcoin,ethereum,defi,solana,ethfinance,ethdev,solidity,CryptoTechnology",
)
MEDIUM_TAGS = _csv(
    "MEDIUM_TAGS",
    "crypto,blockchain,defi,bitcoin,ethereum,solana,web3,smart-contracts,ethereum-development",
)
TELEGRAM_CHANNELS = _csv("TELEGRAM_CHANNELS", "")
BLUESKY_QUERIES = _csv(
    "BLUESKY_QUERIES",
    "crypto satire,crypto parody,crypto irony,funny crypto,funny web3,crypto joke,crypto jokes,crypto comedy,crypto meme,crypto memes,crypto comic,crypto comics,crypto cartoon,crypto shitpost,crypto shitposts,crypto shitposting,crypto humor,web3 humor,crypto be like,web3 be like,crypto irl,crypto in real life,crypto moment,crypto situation",
)

HIGH_PERFORMANCE_MIN_VIEWS = int(os.getenv("HIGH_PERFORMANCE_MIN_VIEWS", "20000"))
HIGH_PERFORMANCE_SEARCH_LIMIT = int(os.getenv("HIGH_PERFORMANCE_SEARCH_LIMIT", "10"))
HIGH_PERFORMANCE_MAX_ITEMS = int(os.getenv("HIGH_PERFORMANCE_MAX_ITEMS", "21"))
