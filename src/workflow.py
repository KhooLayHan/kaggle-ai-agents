import os
import sys
from typing import AsyncGenerator, Generator
from dotenv import load_dotenv

from google.adk import Workflow
from google.adk.runners import InMemoryRunner
from google.adk.events.event import Event
from google.genai import types

# Import the agent definitions
from src.agents import market_analyst_agent, risk_manager_agent, portfolio_manager_agent

load_dotenv()

# Define the ADK workflow graph coordinating the three specialized agents sequentially
trading_workflow = Workflow(
    name="TradingWorkflow",
    edges=[
        ("START", market_analyst_agent),
        (market_analyst_agent, risk_manager_agent),
        (risk_manager_agent, portfolio_manager_agent),
    ]
)

def run_trading_workflow(ticker: str) -> Generator[Event, None, None]:
    """
    Synchronously execute the multi-agent trading workflow using InMemoryRunner.
    Yields events as they occur (including agent content, tool calls, and errors).
    """
    # Create runner with automatic session creation enabled
    runner = InMemoryRunner(trading_workflow)
    runner.auto_create_session = True
    
    # Construct the user message asking for stock analysis on the ticker
    msg = types.Content(
        role="user",
        parts=[
            types.Part.from_text(
                text=f"Analyze the stock symbol: {ticker}. Please retrieve the price, indicators, and news."
            )
        ]
    )
    
    # Run the workflow
    events = runner.run(
        user_id="default_user",
        session_id=f"session_{ticker}",
        new_message=msg
    )
    
    return events
