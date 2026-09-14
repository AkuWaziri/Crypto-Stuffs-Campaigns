import argparse

from demo_data import demo_events
from pipeline import run_demo
from telegram import send_message


def main() -> None:
    parser = argparse.ArgumentParser(description="WhalesBoarder read-only intelligence monitor")
    parser.add_argument("--demo", action="store_true", help="run the complete offline fixture pipeline")
    parser.add_argument("--telegram", action="store_true", help="send generated demo signals to Telegram")
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
    else:
        print("classification=ready")
        print("demo=run with python main.py --demo")


if __name__ == "__main__":
    main()
