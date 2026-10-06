import argparse

from config import HIGH_PERFORMANCE_MAX_ITEMS
from telegram import send_message
from high_performance import search_high_performing_x, mark_sent
from discovery import search_crypto_alpha

def main():
    parser = argparse.ArgumentParser(description="Crypto-Stuffs-Campaigns")
    parser.add_argument("--telegram", action="store_true")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    print("CRYPTO-STUFFS")
    print("mode=read-only")
    print("execution=disabled")
    print("feature=viral_trending_plus_practical_crypto_alpha")
    print("recency=last_7_days")
    print("viral_threshold=20K_views")
    print("viral=50K+_views")
    print(f"max_per_run={HIGH_PERFORMANCE_MAX_ITEMS}")

    try:
        viral_posts = search_high_performing_x()
    except Exception as exc:
        viral_posts = []
        print(f"viral_trending_error={exc}")
    try:
        alpha_posts = search_crypto_alpha()
    except Exception as exc:
        alpha_posts = []
        print(f"crypto_alpha_error={exc}")

    # Reserve slots for both viral posts and practical resources.
    selected = viral_posts[:11] + alpha_posts[:10]
    if len(selected) < HIGH_PERFORMANCE_MAX_ITEMS:
        used = {item.get("id") for item in selected}
        leftovers = [item for item in viral_posts[11:] + alpha_posts[10:] if item.get("id") not in used]
        selected.extend(leftovers[:HIGH_PERFORMANCE_MAX_ITEMS - len(selected)])
    selected = selected[:HIGH_PERFORMANCE_MAX_ITEMS]

    sent_ids = []
    for item in selected:
        if item.get("tier") == "CRYPTO ALPHA":
            message = (
                "🧠 CRYPTO ALPHA: TOOLS, GUIDES & BUILDS\n\n"
                f"SOURCE: {item.get('source', 'web').upper()}\n"
                f"TOPIC: {item.get('niche', 'crypto resources')}\n\n"
                f"{item.get('text', '')[:850]}\n\n"
                f"🔗 {item.get('url', '')}"
            )
        else:
            message = (
                f"🔥 {item.get('tier', 'TRENDING')} CRYPTO POST\n\n"
                f"NICHE: {item.get('niche', 'crypto')}\n"
                f"VIEWS: {item.get('views', 0):,}\n"
                f"FROM: @{item.get('author', 'unknown').lstrip('@')}\n\n"
                f"{item.get('text', '')[:700]}\n\n"
                f"🔗 {item.get('url', '')}"
            )
        delivered = send_message(message, dry_run=not args.telegram or args.test)
        if delivered:
            sent_ids.append(item.get("id"))

    if sent_ids:
        mark_sent(sent_ids)
    print(f"viral_trending_found={len(viral_posts)}")
    print(f"crypto_alpha_found={len(alpha_posts)}")
    print(f"feed_selected={len(selected)}")
    print(f"feed_sent={len(sent_ids)}")

if __name__ == "__main__":
    main()