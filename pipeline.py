from discovery import WhaleCandidate
from evm_monitor import parse_swap_transfer
from feed import format_event
from reason_engine import explain_event
from score import score_signal
from solana_monitor import parse_swap
from stock_monitor import parse_13f_position


def _candidate(row: dict) -> WhaleCandidate:
    return WhaleCandidate(
        wallet=str(row["wallet"]),
        label=None,
        entity_type=str(row.get("type", "WHALE_WALLET")),
        source="demo",
        roi_pct=float(row["roi"]) if row.get("roi") is not None else None,
        win_rate_pct=float(row["winRate"]) if row.get("winRate") is not None else None,
    )


def run_demo(fixtures: list[dict]) -> list[str]:
    outputs: list[str] = []
    for item in fixtures:
        candidate = None
        if item.get("candidate"):
            candidate = _candidate(item["candidate"])
        if item["kind"] == "solana":
            event = parse_swap(item["tx"], item["wallet"], item.get("asset_mint"))
        elif item["kind"] == "evm":
            event = parse_swap_transfer(
                item["tx"], item["wallet"], asset=item.get("asset", "UNKNOWN"), value_usd=item.get("value_usd")
            )
        elif item["kind"] == "stock":
            event = parse_13f_position(item["row"])
        else:
            event = None
        if event is None:
            continue
        if item.get("value_usd") is not None:
            event = type(event)(**{**event.__dict__, "value_usd": item["value_usd"]})
        explanation = explain_event(event)
        signal_score = score_signal(event, explanation, candidate=candidate)
        outputs.append(format_event(event, explanation, signal_score))
    return outputs
