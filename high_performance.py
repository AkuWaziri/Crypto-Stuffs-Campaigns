from datetime import datetime, timedelta, timezone
import re
from tweetkit_x import TweetKit
from tweetkit_x import constants as C
from tweetkit_x.cookie import ct0_of
from tweetkit_x.client import _walk_timeline
from config import X_AUTH_TOKEN, X_CT0, HIGH_PERFORMANCE_SEARCH_LIMIT, HIGH_PERFORMANCE_MIN_VIEWS, HIGH_PERFORMANCE_MAX_ITEMS

CRYPTO_NICHES = (
    "crypto AI", "crypto AI agents", "crypto hack", "crypto hacking",
    "crypto payments", "crypto DeFi", "crypto development", "crypto NFT",
    "crypto nodes", "crypto infrastructure", "crypto onchain findings",
    "crypto research", "crypto security", "crypto smart contracts",
    "crypto builders", "crypto protocols", "crypto wallets",
    "crypto hackathon", "web3 hackathon", "crypto airdrop", "crypto incentives",
    "crypto stablecoins", "crypto trading", "crypto markets", "crypto memecoin",
    "crypto layer 2", "crypto scaling", "crypto DePIN", "crypto restaking",
    "crypto ZK", "crypto privacy", "crypto account abstraction", "crypto interoperability",
    "crypto bridges", "crypto startup", "crypto funding", "crypto launch",
    "crypto ecosystem", "crypto onchain activity", "crypto discoveries", "crypto trends",
)

def _cookie_header():
    if not X_AUTH_TOKEN or not X_CT0:
        raise RuntimeError("X_AUTH_TOKEN and X_CT0 are required")
    return f"auth_token={X_AUTH_TOKEN}; ct0={X_CT0}"

def _iso(value):
    if not value: return None
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%a %b %d %H:%M:%S +0000 %Y").replace(tzinfo=timezone.utc).isoformat()
        except ValueError: return value
    return value

def _number(value):
    if isinstance(value, bool): return None
    if isinstance(value, (int, float)): return int(value)
    if isinstance(value, str):
        m = re.search(r"(\d+(?:\.\d+)?)\s*([km]?)", value.lower().replace(",", ""))
        if not m: return None
        return int(float(m.group(1)) * {"k":1000, "m":1000000}.get(m.group(2), 1))
    return None

def _find_views(obj):
    keys = {"views", "view_count", "viewcount", "impression_count", "impressions"}
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key).lower().replace("-", "_") in keys:
                if isinstance(value, dict):
                    for child in ("count", "view_count", "count_str", "value"):
                        n = _number(value.get(child))
                        if n is not None: return n
                n = _number(value)
                if n is not None: return n
        for value in obj.values():
            n = _find_views(value)
            if n is not None: return n
    elif isinstance(obj, list):
        for value in obj:
            n = _find_views(value)
            if n is not None: return n
    return None

def _tweet_views_by_id(obj, out=None):
    """Extract view counts keyed to tweet ids from the raw X GraphQL tree."""
    out = {} if out is None else out
    if isinstance(obj, dict):
        lg = obj.get("legacy")
        if isinstance(lg, dict) and lg.get("full_text"):
            tid = lg.get("id_str") or obj.get("rest_id")
            if tid:
                views = _find_views(obj)
                if views is not None:
                    out[str(tid)] = views
        for value in obj.values():
            _tweet_views_by_id(value, out)
    elif isinstance(obj, list):
        for value in obj:
            _tweet_views_by_id(value, out)
    return out

def _search(tk, query, limit):
    qid = C.__dict__.get("SEARCH_TIMELINE", "M1jEez78PEfVfbQLvlWMvQ")
    url = f"{C.GQL_BASE}/{qid}/SearchTimeline"
    headers = {"authorization":C.BEARER,"cookie":tk.cookie,"x-csrf-token":ct0_of(tk.cookie),
              "x-twitter-active-user":"yes","x-twitter-auth-type":"OAuth2Session",
              "x-twitter-client-language":"en","accept":"*/*","origin":"https://x.com",
              "referer":"https://x.com/home","user-agent":C.UA,"content-type":"application/json"}
    tweets, users, cursor = {}, {}, None
    for _ in range(2):
        variables = {"rawQuery":query,"count":min(20,limit),"querySource":"typed_query","product":"Latest"}
        if cursor: variables["cursor"] = cursor
        response = tk._session.post(url,json={"variables":variables,"features":C.USER_TWEETS_FEATURES,
            "fieldToggles":{"withArticleRichContentState":False}},headers=headers,timeout=tk.timeout)
        response.raise_for_status()
        raw = response.json()
        view_counts = _tweet_views_by_id(raw)
        before=len(tweets)
        cursor=_walk_timeline(raw,tweets,users)
        for tid, views in view_counts.items():
            if tid in tweets:
                tweets[tid]["views"] = views
        if len(tweets)==before or not cursor or len(tweets)>=limit: break
    return [{**tweet,"author":users.get(tweet.get("author_id"),"unknown"),
             "url":f"https://x.com/{users.get(tweet.get('author_id'),'unknown')}/status/{tweet['id']}"}
            for tweet in tweets.values()]

def _tweet_datetime(tweet):
    raw = tweet.get("created_at")
    try:
        if isinstance(raw, str): return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if isinstance(raw, (int, float)): return datetime.fromtimestamp(raw, timezone.utc)
    except (TypeError, ValueError, OverflowError): pass
    return None

def search_high_performing_x():
    tk=TweetKit(cookie=_cookie_header(),timeout=30)
    found=[]; seen=set()
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    since = cutoff.strftime("%Y-%m-%d")
    for niche in CRYPTO_NICHES:
        try: candidates=_search(tk, f"{niche} since:{since}", HIGH_PERFORMANCE_SEARCH_LIMIT)
        except Exception as exc:
            print(f"high_performance_search_error={niche}: {exc}"); continue
        for tweet in candidates:
            tid=str(tweet.get("id",""))
            if not tid or tid in seen: continue
            seen.add(tid); views=tweet.get("views")
            if views is None:
                try:
                    detail = tk.get_tweet(tid)
                    views = _find_views(detail)
                except Exception as exc:
                    print(f"high_performance_detail_error={tid}: {exc}")
            created = _tweet_datetime(tweet)
            if views is None or views < HIGH_PERFORMANCE_MIN_VIEWS: continue
            if created is None or created < cutoff: continue
            tier = "VIRAL" if views >= 50000 else "TRENDING"
            found.append({"id":tid,"author":tweet.get("author","unknown"),"text":" ".join(str(tweet.get("text","")).split()),
                          "url":tweet.get("url",""),"created_at":_iso(tweet.get("created_at")),
                          "source":"x_high_performance","niche":niche,"views":views,"tier":tier})
    found.sort(key=lambda x: (x["views"], x.get("created_at") or ""), reverse=True)
    return found[:HIGH_PERFORMANCE_MAX_ITEMS]
