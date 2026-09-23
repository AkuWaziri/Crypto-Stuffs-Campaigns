import asyncio
import json
from datetime import timezone
from twscrape import API
from config import X_AUTH_TOKEN, X_CT0, X_SEARCH_LIMIT

X_QUERIES = [
    "crypto (airdrop OR points OR campaign OR rewards OR quest)",
    "crypto (contest OR competition OR bounty OR ambassador OR creator)",
    "crypto (meme OR art OR video OR content) (contest OR campaign OR rewards)",
    "crypto (IDO OR token sale OR launch OR mint OR NFT)",
    "crypto (testnet OR mainnet OR devnet OR builders OR hackathon)",
    "crypto (grant OR application OR applications OR apply)",
]

async def _search():
    if not X_AUTH_TOKEN or not X_CT0:
        raise RuntimeError("X_AUTH_TOKEN and X_CT0 are required")
    api = API("x_scraper.db")
    cookies = json.dumps({"auth_token": X_AUTH_TOKEN, "ct0": X_CT0})
    await api.pool.add_account("scraper_session", "", "", "", cookies=cookies)
    results, seen = [], set()
    for query in X_QUERIES:
        try:
            async for tweet in api.search(query, limit=X_SEARCH_LIMIT):
                if str(tweet.id) in seen:
                    continue
                seen.add(str(tweet.id))
                results.append({
                    "id": str(tweet.id),
                    "author": getattr(tweet.user, "username", "unknown"),
                    "text": tweet.rawContent,
                    "url": tweet.url,
                    "created_at": tweet.date.astimezone(timezone.utc).isoformat(),
                    "source": "x",
                })
        except Exception as exc:
            print(f"x_search_error={query}: {exc}")
    return results

def search_x():
    return asyncio.run(_search())
