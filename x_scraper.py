from datetime import datetime, timezone
from tweetkit_x import TweetKit
from config import X_AUTH_TOKEN, X_CT0, X_SEARCH_LIMIT

X_QUERIES = [
    "crypto (airdrop OR points OR campaign OR rewards OR quest)",
    "crypto (contest OR competition OR bounty OR ambassador OR creator)",
    "crypto (meme OR art OR video OR content) (contest OR campaign OR rewards)",
    "crypto (IDO OR token sale OR launch OR mint OR NFT)",
    "crypto (testnet OR mainnet OR devnet OR builders OR hackathon)",
    "crypto (grant OR application OR applications OR apply)",
]


def _cookie_header():
    if not X_AUTH_TOKEN or not X_CT0:
        raise RuntimeError("X_AUTH_TOKEN and X_CT0 are required")
    return f"auth_token={X_AUTH_TOKEN}; ct0={X_CT0}"


def _iso_created_at(value):
    if not value:
        return None
    try:
        dt = datetime.strptime(value, "%a %b %d %H:%M:%S +0000 %Y")
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return value


def search_x():
    tk = TweetKit(cookie=_cookie_header(), timeout=30)
    results = []
    seen = set()

    for query in X_QUERIES:
        try:
            tweets = tk.search_x(query, product="Latest", limit=X_SEARCH_LIMIT)
            for tweet in tweets:
                tweet_id = str(tweet.get("id", ""))
                if not tweet_id or tweet_id in seen:
                    continue
                seen.add(tweet_id)
                results.append({
                    "id": tweet_id,
                    "author": tweet.get("author", "unknown"),
                    "text": tweet.get("text", ""),
                    "url": tweet.get("url", ""),
                    "created_at": _iso_created_at(tweet.get("created_at")),
                    "source": "x",
                })
        except Exception as exc:
            print(f"x_search_error={query}: {exc}")

    return results
