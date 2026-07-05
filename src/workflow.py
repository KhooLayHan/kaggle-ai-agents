"""ADK workflow runner that drives the sequential Market Analyst → Risk Manager → Portfolio Manager pipeline."""

from typing import Generator

from dotenv import load_dotenv

from google.adk.runners import InMemoryRunner
from google.adk.events.event import Event
from google.genai import types

from src.agents.trading_agent.agent import trading_workflow

load_dotenv()


def run_trading_workflow(ticker: str) -> Generator[Event, None, None]:
    """
    Synchronously execute the multi-agent trading workflow using InMemoryRunner.
    Yields events as they occur (including agent content, tool calls, and errors).
    """
    runner = InMemoryRunner(trading_workflow)
    runner.auto_create_session = True

    msg = types.Content(
        role="user",
        parts=[
            types.Part.from_text(
                text=f"Analyze the stock symbol: {ticker}. Please retrieve the price, indicators, and news."
            )
        ]
    )

    events = runner.run(
        user_id="default_user",
        session_id=f"session_{ticker}",
        new_message=msg
    )

    return events
