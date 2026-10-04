import argparse

from config import HIGH_PERFORMANCE_MAX_ITEMS
from telegram import send_message
from high_performance import search_high_performing_x, mark_sent

def main():
    parser = argparse.ArgumentParser(description="Crypto-Stuffs-Campaigns")
    parser.add_argument("--telegram", action="store_true")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    print("CRYPTO-STUFFS")
    print("mode=read-only")
    print("execution=disabled")
    print("feature=viral_and_trending_crypto_posts")
    print("recency=last_7_days")
    print("threshold=20K_views")
    print("viral=50K+_views")
    print(f"max_per_run={HIGH_PERFORMANCE_MAX_ITEMS}")

    try:
        posts = search_high_performing_x()
        selected = posts[:HIGH_PERFORMANCE_MAX_ITEMS]
        sent_ids = []
        for item in selected:
            tier = item.get("tier", "TRENDING")
            delivered = send_message(
                f"🔥 {tier} CRYPTO POST\n\n"
                f"NICHE: {item.get('niche', 'crypto')}\n"
                f"VIEWS: {item.get('views', 0):,}\n"
                f"FROM: @{item.get('author', 'unknown').lstrip('@')}\n\n"
                f"{item.get('text', '')[:700]}\n\n"
                f"🔗 {item.get('url', '')}",
                dry_run=not args.telegram or args.test,
            )
            if delivered:
                sent_ids.append(item.get("id"))
        if sent_ids:
            mark_sent(sent_ids)
        print(f"viral_trending_found={len(posts)}")
        print(f"viral_trending_sent={len(selected)}")
    except Exception as exc:
        print(f"viral_trending_error={exc}")

if __name__ == "__main__":
    main()
