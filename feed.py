def format_item(item):
    source = item.get("source", "unknown").upper()
    types = ", ".join(item.get("types", [])) or "crypto"
    author = item.get("author", "unknown")
    text = " ".join(item.get("text", "").split())
    if len(text) > 700:
        text = text[:697] + "..."
    author_text = str(author)
    if source == "X" and not author_text.startswith("@"):
        author_text = "@" + author_text
    return (
        "🛰️ CRYPTO-STUFFS\n\n"
        f"SOURCE: {source}\nTYPE: {types}\nFROM: {author_text}\n\n"
        f"{text}\n\n🔗 {item.get('url', '')}"
    )
