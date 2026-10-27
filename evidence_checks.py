"""Deterministic checks that generated concrete claims appear in supplied source material.

These checks are conservative consistency guards, not proof that a source is true.
"""
import re


URL_RE = re.compile(r"https?://\S+", re.I)
ADDRESS_RE = re.compile(r"\b0x[a-fA-F0-9]{8,}\b")
# Match numbers that commonly carry factual weight. Small step numbers are
# intentionally excluded so numbered how-to instructions remain usable.
FACT_NUMBER_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:\$|€|£)?"
    r"(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d{3,}(?:\.\d+)?|\d+\.\d+)"
    r"(?:\s?%|\s?(?:million|billion|thousand|usd|usdc|eth|btc|days?|hours?|users?|transactions?| wallets?))?",
    re.I,
)


def _without_urls(value):
    return URL_RE.sub(" ", str(value or ""))


def _normal_number(value):
    return re.sub(r"[,\s]", "", value).lower()


def check_draft_against_evidence(draft, evidence):
    """Return (ok, reason) if key addresses/numbers in a draft occur in evidence.

    Exact literal matching is deliberate: paraphrases can pass, but invented
    figures and contract addresses are held for review rather than published.
    """
    body = _without_urls(draft)
    source = _without_urls(evidence).lower()

    for address in ADDRESS_RE.findall(body):
        if address.lower() not in source:
            return False, "unsupported_address"

    source_numbers = list(FACT_NUMBER_RE.finditer(source))
    unit_pattern = re.compile(
        r"(%|million|billion|thousand|usd|usdc|eth|btc|days?|hours?|users?|transactions?|wallets?)",
        re.I,
    )

    for match in FACT_NUMBER_RE.finditer(body):
        literal = match.group(0).strip()
        digits = re.sub(r"\D", "", literal)
        # Ignore small bare integers such as numbered list steps.
        if not any(char in literal for char in "%.$€£") and not unit_pattern.search(literal) and len(digits) < 3 and "." not in literal:
            continue

        numeric_core = _normal_number(re.sub(r"[^\d.,]", "", literal))
        draft_unit_match = unit_pattern.search(literal)
        draft_unit = draft_unit_match.group(1).lower() if draft_unit_match else None
        supported = False
        for source_match in source_numbers:
            source_literal = source_match.group(0).strip()
            source_core = _normal_number(re.sub(r"[^\d.,]", "", source_literal))
            source_unit_match = unit_pattern.search(source_literal)
            source_unit = source_unit_match.group(1).lower() if source_unit_match else None
            # Require the numeric token itself to match, not merely appear as
            # a substring of another value (for example 100 inside 1,100).
            if numeric_core != source_core:
                continue
            # A stated unit/percent must agree; 100 ETH cannot support 100 USDC.
            if draft_unit and draft_unit != source_unit:
                continue
            supported = True
            break
        if not supported:
            return False, "unsupported_numeric_claim"

    return True, "supported_literals"
