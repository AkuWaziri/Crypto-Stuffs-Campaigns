import argparse

from demo_data import demo_events
from evm_live import EVM_DIAGNOSTICS, event_key, explain_evm_event, fetch_recent_large_evm_trades
from feed import format_event
from live_state import load_seen_keys, remember_keys
from pipeline import run_demo
from score import score_signal
from solana_discovery import discover_solana_events, explain_discovered_event
from telegram import send_message


def main() -> None:
    parser = argparse.ArgumentParser(description="WhalesBoarder read-only intelligence monitor")
    parser.add_argument("--demo", action="store_true", help="run the complete offline fixture pipeline")
    parser.add_argument("--telegram", action="store_true", help="send generated signals to Telegram")
    parser.add_argument("--live", action="store_true", help="poll live Solana and EVM whale activity")
    args = parser.parse_args()

    print("WHALESBOARDER")
    print("mode=read-only")
    print("execution=disabled")
    print("chains=solana,evm")
    print("stocks=public-disclosure")

    if args.demo:
        outputs = run_demo(demo_events())
        for output in outputs:
            send_message(output, dry_run=not args.telegram)
        print(f"demo_signals={len(outputs)}")
        print(f"telegram={'enabled' if args.telegram else 'dry-run'}")
        return

    if args.live:
        seen = load_seen_keys()
        solana_events = discover_solana_events()
        evm_events = fetch_recent_large_evm_trades()
        events = solana_events + evm_events
        new_events = []
        new_keys = set()

        for event in events:
            key = event_key(event)
            if key in seen or key in new_keys:
                continue
            new_events.append(event)
            new_keys.add(key)

        for event in new_events:
            if event.chain == "solana":
                explanation = explain_discovered_event(event, solana_events)
            else:
                explanation = explain_evm_event(event)
            signal_score = score_signal(event, explanation)
            output = format_event(event, explanation, signal_score)
            send_message(output, dry_run=not args.telegram)

        if new_keys:
            remember_keys(new_keys)

        for diagnostic in EVM_DIAGNOSTICS:
            print(f"evm_diagnostic={diagnostic}")

        print(f"live_signals={len(new_events)}")
        print(f"solana_signals={sum(1 for event in new_events if event.chain == 'solana')}")
        print(f"evm_signals={sum(1 for event in new_events if event.chain != 'solana')}")
        print(f"duplicates_skipped={len(events) - len(new_events)}")
        print(f"telegram={'enabled' if args.telegram else 'dry-run'}")
        return

    print("classification=ready")
    print("demo=run with python main.py --demo")
    print("live=run with python main.py --live --telegram")


if __name__ == "__main__":
    main()
