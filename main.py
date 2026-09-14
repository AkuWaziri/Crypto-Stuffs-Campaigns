import argparse

from demo_data import demo_events
from feed import format_event
from pipeline import run_demo
from score import score_signal
from telegram import send_message
from vybe_live import collect_vybe_live_events, explain_live_event


def main() -> None:
    parser = argparse.ArgumentParser(description="WhalesBoarder read-only intelligence monitor")
    parser.add_argument("--demo", action="store_true", help="run the complete offline fixture pipeline")
    parser.add_argument("--telegram", action="store_true", help="send generated signals to Telegram")
    parser.add_argument("--live", action="store_true", help="poll live Solana whale activity")
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
        events = collect_vybe_live_events()
        for event in events:
            explanation = explain_live_event(event)
            signal_score = score_signal(event, explanation)
            output = format_event(event, explanation, signal_score)
            send_message(output, dry_run=not args.telegram)
        print(f"live_signals={len(events)}")
        print(f"telegram={'enabled' if args.telegram else 'dry-run'}")
        return

    print("classification=ready")
    print("demo=run with python main.py --demo")
    print("live=run with python main.py --live --telegram")


if __name__ == "__main__":
    main()
