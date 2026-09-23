def format_item(item):
    source = item.get("source", "unknown").upper()
    types = ", ".join(item.get("types", []))
    author = item.get("author", "unknown")
    text = " ".join(item.get("text", "").split())
    if len(text) > 700:
        text = text[:697] + "..."
    return (
        "🛰️ CRYPTO-STUFFS CAMPAIGNS\n\n"
        f"SOURCE: {source}\nTYPE: {types}\nFROM: @{author}\n"
        f"SIGNAL: {item.get('campaign_score', 0)}/100\n\n{text}\n\n"
        f"🔗 {item.get('url', '')}"
    )
