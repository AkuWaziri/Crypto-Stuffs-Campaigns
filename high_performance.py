from datetime import datetime, timedelta, timezone
import json
import os
import re
import hashlib
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from tweetkit_x import TweetKit
from tweetkit_x import constants as C
from tweetkit_x.cookie import ct0_of
from tweetkit_x.client import _walk_timeline
from config import X_AUTH_TOKEN, X_CT0, HIGH_PERFORMANCE_SEARCH_LIMIT, HIGH_PERFORMANCE_MIN_VIEWS, HIGH_PERFORMANCE_MAX_ITEMS

SEEN_STATE_FILE = os.getenv("VIRAL_SEEN_STATE_FILE", ".viral_trending_seen.json")
SEEN_STATE_LIMIT = 10000

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

def _detail_views(tk, tweet_id):
    """Fetch one tweet raw GraphQL result without TweetKit transaction-id helper."""
    qid = "aFvUsJm2c-oDkJV75blV6g"
    url = f"{C.GQL_BASE}/{qid}/TweetResultByRestId"
    headers = {"authorization": C.BEARER, "cookie": tk.cookie, "x-csrf-token": ct0_of(tk.cookie),
               "x-twitter-active-user": "yes", "x-twitter-auth-type": "OAuth2Session",
               "x-twitter-client-language": "en", "accept": "*/*", "origin": "https://x.com",
               "referer": "https://x.com/home", "user-agent": C.UA}
    variables = {"tweetId": str(tweet_id), "withCommunity": False,
                 "includePromotedContent": False, "withVoice": False}
    import json
    params = {"variables": json.dumps(variables),
              "features": json.dumps(C.USER_TWEETS_FEATURES),
              "fieldToggles": json.dumps({"withArticleRichContentState": False})}
    response = tk._session.get(url, params=params, headers=headers, timeout=tk.timeout)
    response.raise_for_status()
    return _tweet_views_by_id(response.json()).get(str(tweet_id))

def _tweet_datetime(tweet):
    raw = tweet.get("created_at")
    try:
        if isinstance(raw, str):
            try:
                return datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                return datetime.strptime(
                    raw, "%a %b %d %H:%M:%S +0000 %Y"
                ).replace(tzinfo=timezone.utc)
        if isinstance(raw, (int, float)):
            return datetime.fromtimestamp(raw, timezone.utc)
    except (TypeError, ValueError, OverflowError):
        pass
    return None

def _item_key(item):
    """Return a normalized content fingerprint robust to whitespace and tracking markup."""
    text = str(item.get("text", "")).lower()
    text = re.sub(r"https?://\S+, " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = " ".join(text.split())
    # The leading phrase is usually the article/post headline. Using it avoids
    # duplicates when RSS tags attach different snippets to the same article.
    identity = text[:240] if text else ""
    url = _canonical_url(item.get("url", ""))
    value = identity or url
    return ("text:" if identity else "url:") + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_url(value):
    """Remove tracking parameters so the same source URL has one stable identity."""
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parts = urlsplit(raw)
        if not parts.scheme or not parts.netloc:
            return raw.rstrip("/")
        tracking = {"source", "ref", "ref_src", "fbclid", "gclid", "mc_cid", "mc_eid"}
        query = [
            (key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True)
            if not key.lower().startswith("utm_") and key.lower() not in tracking
        ]
        path = parts.path.rstrip("/") or "/"
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))
    except (TypeError, ValueError):
        return raw.rstrip("/")


def _url_key(item):
    """Return a stable URL key independent of common analytics/tracking parameters."""
    url = _canonical_url(item.get("url", ""))
    return "url:" + hashlib.sha256(url.encode("utf-8")).hexdigest() if url else ""

def _load_seen_ids():
    try:
        with open(SEEN_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        ids = {str(x) for x in data.get("sent_ids", []) if x}
        keys = {str(x) for x in data.get("sent_keys", []) if x}
        return ids | keys
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return set()

def mark_sent(items):
    """Persist both source IDs and content fingerprints after Telegram accepts delivery."""
    try:
        with open(SEEN_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        data = {}

    ids = {str(x) for x in data.get("sent_ids", []) if x}
    keys = {str(x) for x in data.get("sent_keys", []) if x}

    for item in items:
        if isinstance(item, dict):
            item_id = item.get("id")
            if item_id:
                ids.add(str(item_id))
            keys.add(_item_key(item))
            url_key = _url_key(item)
            if url_key:
                keys.add(url_key)
        elif item:
            ids.add(str(item))

    data = {
        "sent_ids": list(ids)[-SEEN_STATE_LIMIT:],
        "sent_keys": list(keys)[-SEEN_STATE_LIMIT:],
    }
    tmp = f"{SEEN_STATE_FILE}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, SEEN_STATE_FILE)

def search_high_performing_x():
    tk=TweetKit(cookie=_cookie_header(),timeout=30)
    found=[]; seen=set(); sent_keys=_load_seen_ids()
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    since = cutoff.strftime("%Y-%m-%d")
    for niche in CRYPTO_NICHES:
        try: candidates=_search(tk, f"{niche} since:{since}", HIGH_PERFORMANCE_SEARCH_LIMIT)
        except Exception as exc:
            print(f"high_performance_search_error={niche}: {exc}"); continue
        for tweet in candidates:
            tid=str(tweet.get("id",""))
            if not tid or tid in seen: continue
            seen.add(tid)
            candidate = {
                "id": tid,
                "author": tweet.get("author","unknown"),
                "text": " ".join(str(tweet.get("text","")).split()),
                "url": tweet.get("url",""),
            }
            if tid in sent_keys or _item_key(candidate) in sent_keys:
                continue
            views=tweet.get("views")
            if views is None:
                try:
                    views = _detail_views(tk, tid)
                except Exception as exc:
                    print(f"high_performance_detail_error={tid}: {exc}")
            created = _tweet_datetime(tweet)
            if views is None or views < 1000: continue
            if created is None or created < cutoff: continue
            is_trending = views >= HIGH_PERFORMANCE_MIN_VIEWS
            tier = ("VIRAL" if views >= 50000 else "TRENDING") if is_trending else "SOCIAL"
            found.append({"id":tid,"author":tweet.get("author","unknown"),"text":" ".join(str(tweet.get("text","")).split()),
                          "url":tweet.get("url",""),"created_at":_iso(tweet.get("created_at")),
                          "source":"x_high_performance" if is_trending else "x_social",
                          "niche":niche,"views":views,"tier":tier})
    trending = sorted(
        (x for x in found if x["source"] == "x_high_performance"),
        key=lambda x: (x["views"], x.get("created_at") or ""), reverse=True,
    )
    social = sorted(
        (x for x in found if x["source"] == "x_social"),
        key=lambda x: (x.get("created_at") or "", x["views"]), reverse=True,
    )
    trending = trending[:HIGH_PERFORMANCE_MAX_ITEMS]
    social_limit = max(0, HIGH_PERFORMANCE_MAX_ITEMS - len(trending))
    result = trending + social[:social_limit]
    print(f"x_trending_candidates={len(trending)}")
    print(f"x_social_candidates={min(len(social), social_limit)}")
    return result
