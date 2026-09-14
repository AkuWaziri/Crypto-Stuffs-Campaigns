from models import ActivityEvent, Explanation


def format_event(event: ActivityEvent, explanation: Explanation, score: int) -> str:
    action_icon = {"BUY": "🟢", "SELL": "🔴", "TRANSFER": "🔵", "UNKNOWN": "⚪"}[event.action]
    value = f"~${event.value_usd:,.0f}" if event.value_usd is not None else "Unknown"
    evidence = "\n".join(f"• {item}" for item in explanation.evidence) or "• No external evidence"
    return (
        "🐋 WHALESBOARDER\n\n"
        f"{action_icon} {event.action}\n"
        f"WHO: {event.entity}\n"
        f"ASSET: {event.asset}\n"
        f"VALUE: {value}\n"
        f"CHAIN: {event.chain or 'Unknown'}\n"
        f"TIME: {event.timestamp.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        "WHY IT MAY MATTER\n"
        f"{explanation.reason}\n\n"
        "POSSIBLE REASON\n"
        f"{explanation.reason}\n\n"
        "EVIDENCE\n"
        f"{evidence}\n\n"
        f"CONFIDENCE: {explanation.confidence}\n"
        f"SIGNAL SCORE: {score}/100"
    )
