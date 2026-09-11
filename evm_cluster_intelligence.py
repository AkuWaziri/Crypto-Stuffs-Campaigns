"""Cross-layer address clustering and coordination evidence."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable

@dataclass(frozen=True)
class ClusterReport:
    addresses: tuple[str, ...]
    overlap_count: int
    overlap_addresses: tuple[str, ...] = field(default_factory=tuple)
    signals: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

def _norm(values: Iterable[str]) -> set[str]:
    out = set()
    for value in values:
        if isinstance(value, str) and len(value) == 42 and value.startswith("0x"):
            try:
                int(value[2:], 16)
            except ValueError:
                continue
            out.add("0x" + value[2:].lower())
    return out

def inspect_address_clusters(*, holder_addresses: Iterable[str] = (), early_buyer_addresses: Iterable[str] = (), funding_sender_addresses: Iterable[str] = (), funding_receiver_addresses: Iterable[str] = (), excluded_addresses: Iterable[str] = ()) -> ClusterReport:
    holder = _norm(holder_addresses)
    early = _norm(early_buyer_addresses)
    senders = _norm(funding_sender_addresses)
    receivers = _norm(funding_receiver_addresses)
    excluded = _norm(excluded_addresses)
    overlap = (early & (senders | receivers)) | (holder & (senders | receivers))
    overlap -= excluded
    all_addresses = holder | early | senders | receivers
    signals = []
    if early & (senders | receivers):
        signals.append("EARLY_BUYER_FUNDING_OVERLAP")
    if holder & (senders | receivers):
        signals.append("HOLDER_FLOW_OVERLAP")
    if len(overlap) >= 3:
        signals.append("MULTI_ADDRESS_CLUSTER_OVERLAP")
    warnings = ["CLUSTER_EVIDENCE_IS_OBSERVATIONAL"]
    if not all_addresses:
        warnings.append("NO_CLUSTER_ADDRESSES")
    return ClusterReport(tuple(sorted(all_addresses)), len(overlap), tuple(sorted(overlap)), tuple(signals), tuple(warnings))
