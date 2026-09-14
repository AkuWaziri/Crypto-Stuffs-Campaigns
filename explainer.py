from models import Explanation


def explain_activity(*, direct_reason: str | None = None, contextual_reason: str | None = None, evidence: tuple[str, ...] = ()) -> Explanation:
    if direct_reason:
        return Explanation("CONFIRMED", direct_reason, evidence, "HIGH")
    if contextual_reason:
        return Explanation("INFERRED", contextual_reason, evidence, "MEDIUM")
    return Explanation("UNKNOWN", "No reliable reason identified", evidence, "LOW")
