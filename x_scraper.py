from datetime import datetime, timezone
from tweetkit_x import TweetKit
from config import X_AUTH_TOKEN, X_CT0, X_SEARCH_LIMIT

# Keep queries deliberately simple. tweetkit-x passes these through X's
# web SearchTimeline request, and complex boolean/grouped expressions can
# break its current query handling before the request is sent.
X_QUERIES = [
    "crypto airdrop",
    "crypto points",
    "crypto campaign",
    "crypto rewards",
    "crypto quest",
    "crypto contest",
    "crypto competition",
    "crypto bounty",
    "crypto ambassador",
    "crypto creator",
    "crypto meme contest",
    "crypto art contest",
    "crypto video contest",
    "crypto content campaign",
    "crypto IDO",
    "crypto token sale",
    "crypto NFT mint",
    "crypto testnet",
    "crypto mainnet",
    "crypto devnet",
    "crypto builders",
    "crypto hackathon",
    "crypto grant",
    "crypto apply",
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
