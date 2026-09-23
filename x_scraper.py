from datetime import datetime, timezone
import json

from tweetkit_x import TweetKit
from tweetkit_x import constants as C
from tweetkit_x.cookie import ct0_of
from tweetkit_x.client import _walk_timeline
from config import X_AUTH_TOKEN, X_CT0, X_SEARCH_LIMIT, X_SEARCH_QUERY_ID

X_QUERIES = [
    "crypto airdrop", "crypto points", "crypto campaign", "crypto rewards",
    "crypto quest", "crypto contest", "crypto competition", "crypto bounty",
    "crypto ambassador", "crypto creator", "crypto meme contest",
    "crypto art contest", "crypto video contest", "crypto content campaign",
    "crypto IDO", "crypto token sale", "crypto NFT mint", "crypto testnet",
    "crypto mainnet", "crypto devnet", "crypto builders", "crypto hackathon",
    "crypto grant", "crypto apply",
]

def _cookie_header():
    if not X_AUTH_TOKEN or not X_CT0:
        raise RuntimeError("X_AUTH_TOKEN and X_CT0 are required")
    return f"auth_token={X_AUTH_TOKEN}; ct0={X_CT0}"

def _iso_created_at(value):
    if not value:
        return None
    if isinstance(value, str):
        try:
            dt = datetime.strptime(value, "%a %b %d %H:%M:%S +0000 %Y")
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            return value
    return value

def _search_without_transaction(tk, query, limit):
    # SearchTimeline currently uses POST. Keep the query ID configurable.
    qid = X_SEARCH_QUERY_ID or "GcXk9vN_d1jUfHNqLacXQA"
    url = f"{C.GQL_BASE}/{qid}/SearchTimeline"

    headers = {
        "authorization": C.BEARER,
        "cookie": tk.cookie,
        "x-csrf-token": ct0_of(tk.cookie),
        "x-twitter-active-user": "yes",
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-client-language": "en",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://x.com",
        "referer": "https://x.com/home",
        "user-agent": C.UA,
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "content-type": "application/json",
    }

    tweets, users, cursor, pages = {}, {}, None, 0
    while len(tweets) < limit and pages < 3:
        pages += 1
        variables = {
            "rawQuery": query,
            "count": min(20, limit),
            "querySource": "typed_query",
            "product": "Latest",
        }
        if cursor:
            variables["cursor"] = cursor

        payload = {
            "variables": variables,
            "features": C.USER_TWEETS_FEATURES,
            "fieldToggles": {"withArticleRichContentState": False},
        }

        response = tk._session.post(
            url,
            json=payload,
            headers=headers,
            timeout=tk.timeout,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"SearchTimeline HTTP {response.status_code}: {response.text[:200]}"
            )

        before = len(tweets)
        next_cursor = _walk_timeline(response.json(), tweets, users)
        if len(tweets) == before or not next_cursor:
            break
        cursor = next_cursor

    output = []
    for tweet in tweets.values():
        handle = users.get(tweet["author_id"], "unknown")
        output.append({
            **tweet,
            "author": handle,
            "url": f"https://x.com/{handle}/status/{tweet['id']}",
        })

    output.sort(key=lambda item: item.get("created_at_ts", 0), reverse=True)
    return output[:limit]

def search_x():
    tk = TweetKit(cookie=_cookie_header(), timeout=30)
    results, seen = [], set()

    for query in X_QUERIES:
        try:
            tweets = _search_without_transaction(tk, query, X_SEARCH_LIMIT)
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
