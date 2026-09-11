from __future__ import annotations

from dataclasses import dataclass

from config import TOKEN_LAUNCH_ENABLED
from token_concept import TokenConcept


@dataclass(frozen=True)
class LaunchRequest:
    concept: TokenConcept


class LaunchProvider:
    """Explicit launch boundary. No implementation is provided in the intelligence phase."""

    def launch(self, request: LaunchRequest) -> str:
        raise RuntimeError("token launch provider is not implemented")


def prepare_launch_request(concept: TokenConcept) -> LaunchRequest | None:
    if not TOKEN_LAUNCH_ENABLED:
        return None
    return LaunchRequest(concept)
