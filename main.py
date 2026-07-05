"""Entry point dispatcher for the AI Agent Trading System.

Usage:
  python main.py                      Print help and available commands.
  python main.py --ticker AAPL        Analyze a ticker via the legacy rich CLI.
  python main.py --web                Launch the ADK web playground.

The primary run path is `adk web` / `adk run trading_agent` (see README.md).
This dispatcher exists so `python main.py` is never a dead-end stub.
"""

import argparse
import subprocess
from src.cli import run_agent_cli


def main():
    """Temp"""
    parser = argparse.ArgumentParser(
        description="AI Agent Trading & Market Analysis System",
        epilog="Primary run path: `adk web` or `adk run trading_agent`",
    )
    parser.add_argument(
        "--ticker",
        type=str,
        help="Stock ticker symbol to analyze (e.g. AAPL, GOOGL, MSFT)",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch the ADK web playground (adk web)",
    )
    args = parser.parse_args()

    if args.web:
        subprocess.run(["adk", "web"], check=False)
        return

    if args.ticker:
        run_agent_cli(args.ticker)
        return

    parser.print_help()
    print(
        "\nPrimary run path: `adk web` (browser playground) "
        "or `adk run trading_agent` (headless session)."
    )


if __name__ == "__main__":
    main()
