from __future__ import annotations

from datetime import datetime, timezone

from config import MAX_LAUNCHES_PER_CYCLE, MAX_SIGNAL_AGE_MINUTES, MODE
from pipeline import run_cycle


def main() -> None:
    now = datetime.now(timezone.utc)
    signals, narratives, verifications, qualifications, assessments, intelligence, launch_plans = run_cycle(now=now)

    print("=== TRENDSBOT OBSERVATION ===")
    print(f"mode={MODE}; execution=disabled; max_signal_age_minutes={MAX_SIGNAL_AGE_MINUTES}")
    print(f"signals={len(signals)} narratives={len(narratives)} qualified={len(intelligence)} plans={len(launch_plans)}")
    print()

    if not launch_plans:
        print("No qualified recent trend produced a research launch plan in this cycle.")
        return

    for index, plan in enumerate(launch_plans[:MAX_LAUNCHES_PER_CYCLE], start=1):
        concept = plan.pairing.concept
        stock = plan.pairing.stock
        print(f"#{index} {concept.name}")
        print(f"trend_score={plan.intelligence_score:.2f}")
        print(f"concept=${concept.symbol}")
        print(f"paired_xstock={stock.symbol} ({stock.name})")
        print(f"stock_status={stock.availability}")
        print(f"source_signals={len(concept.source_signal_ids)}")
        print(f"thesis={concept.thesis}")
        print(f"reason={plan.pairing.reason}")
        print()


if __name__ == "__main__":
    main()
