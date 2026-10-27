"""Deterministic checks that generated concrete claims appear in supplied source material.

These checks are conservative consistency guards, not proof that a source is true.
"""
import re
from urllib.parse import urlparse


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

    for match in FACT_NUMBER_RE.finditer(body):
        literal = match.group(0).strip()
        digits = re.sub(r"\D", "", literal)
        # Ignore small bare integers such as numbered list steps.
        if not any(char in literal for char in "%.$€£") and not re.search(
            r"\b(?:million|billion|thousand|usd|usdc|eth|btc|days?|hours?|users?|transactions?|wallets?)\b",
            literal,
            re.I,
        ) and len(digits) < 3 and "." not in literal:
            continue
        normalized = _normal_number(literal)
        if normalized not in source:
            # Currency/unit text may differ in source formatting; require the
            # numeric core too, but never accept a number absent from evidence.
            numeric_core = _normal_number(re.sub(r"[^\d.,]", "", literal))
            if not numeric_core or numeric_core not in re.sub(r"[^\d.,]", "", source):
                return False, "unsupported_numeric_claim"

    return True, "supported_literals"
