from models import ActivityEvent, Explanation


def _why_it_matters(event: ActivityEvent) -> str:
    if event.action == "BUY":
        if event.value_usd is not None:
            return f"A ~${event.value_usd:,.0f} purchase by this tracked wallet may indicate meaningful accumulation or portfolio positioning."
        return "A purchase by this tracked wallet may indicate meaningful accumulation or portfolio positioning."
    if event.action == "SELL":
        if event.value_usd is not None:
            return f"A ~${event.value_usd:,.0f} disposal by this tracked wallet may indicate profit-taking, portfolio rotation, or reduced exposure."
        return "A disposal by this tracked wallet may indicate profit-taking, portfolio rotation, or reduced exposure."
    if event.action == "TRANSFER":
        return "The wallet moved the tracked asset, but the movement does not by itself prove a trade."
    return "The activity is notable, but the available data does not reliably establish a buy or sell."


def _possible_reason(explanation: Explanation) -> str:
    if explanation.status == "INFERRED":
        return explanation.reason
    return "No reliable reason identified from the available transaction data."


def _identity(event: ActivityEvent) -> str:
    if event.chain != "public-disclosure":
        return f"WHO: {event.entity}\nADDRESS: {event.entity}"
    return f"WHO: {event.entity}"


def format_event(event: ActivityEvent, explanation: Explanation, score: int) -> str:
    action_icon = {"BUY": "🟢", "SELL": "🔴", "TRANSFER": "🔵", "UNKNOWN": "⚪"}[event.action]
    value = f"~${event.value_usd:,.0f}" if event.value_usd is not None else "Unknown"
    evidence = "\n".join(f"• {item}" for item in explanation.evidence) or "• No external evidence"
    return (
        "🐋 WHALESBOARDER\n\n"
        f"{action_icon} {event.action}\n"
        f"{_identity(event)}\n"
        f"ASSET: {event.asset}\n"
        f"VALUE: {value}\n"
        f"CHAIN: {event.chain or 'Unknown'}\n"
        f"TIME: {event.timestamp.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        "WHY IT MAY MATTER\n"
        f"{_why_it_matters(event)}\n\n"
        "POSSIBLE REASON\n"
        f"{_possible_reason(explanation)}\n\n"
        "EVIDENCE\n"
        f"{evidence}\n\n"
        f"CONFIDENCE: {explanation.confidence}\n"
        f"SIGNAL SCORE: {score}/100"
    )
