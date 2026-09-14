from models import ActivityEvent, Explanation


def explain_event(event: ActivityEvent, *, contextual_reason: str | None = None) -> Explanation:
    """Explain only what the event evidence supports."""
    if event.action in {"BUY", "SELL"}:
        if event.source in {"helius", "evm_provider"} and event.tx_or_reference:
            return Explanation(
                "CONFIRMED",
                f"Transaction data confirms a {event.action.lower()} of {event.asset}.",
                event.evidence,
                "HIGH",
            )
        if event.source == "sec_13f":
            return Explanation(
                "CONFIRMED",
                f"Public disclosure records a {event.action.lower()} position change in {event.asset}; exact execution timing is not established.",
                event.evidence,
                "MEDIUM",
            )
    if contextual_reason:
        return Explanation("INFERRED", contextual_reason, event.evidence, "MEDIUM")
    return Explanation("UNKNOWN", "No reliable reason identified", event.evidence, "LOW")
