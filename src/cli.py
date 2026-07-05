"""Legacy rich-console CLI for the multi-agent trading system with pre/post guardrails."""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.status import Status

from src.exceptions import WorkflowExecutionError
from src.security import sanitize_ticker, sanitize_and_format_output
from src.workflow import run_trading_workflow

console = Console()

def run_agent_cli(ticker: str):
    """
    Run stock market trading multi-agent system on a specified ticker symbol.
    """
    # Step 1: Input validation
    is_valid, clean_ticker = sanitize_ticker(ticker)
    if not is_valid:
        console.print(Panel(
            f"[bold red]Security Guardrail Alert:[/bold red] Symbol '{ticker}' is invalid.\n"
            "Ticker symbols must contain only 1-5 letters (optionally with a dot or hyphen).",
            title="Input Validation Failed",
            border_style="red"
        ))
        sys.exit(1)

    console.print(Panel(
        f"Initializing Multi-Agent system to analyze stock: [bold cyan]{clean_ticker}[/bold cyan]...\n"
        "Agents Involved:\n"
        "  - [bold yellow]MarketAnalystAgent[/bold yellow] (MCP tools: Price, Indicators, News)\n"
        "  - [bold magenta]RiskManagerAgent[/bold magenta] (Risk guidelines, limits, and stops)\n"
        "  - [bold green]PortfolioManagerAgent[/bold green] (Final BUY/SELL/HOLD decision and disclaimers)",
        title="AI Agent Trading System",
        border_style="blue"
    ))

    # Run the workflow and print streaming events
    try:
        events = run_trading_workflow(clean_ticker)

        current_agent = None
        agent_buffer = ""

        # We will parse events as they arrive
        with Status(f"Analyzing {clean_ticker} using ADK Workflow...", spinner="dots") as status:
            for event in events:
                # Update status message if agents are switching
                if event.author and event.author != current_agent:
                    # Print completed agent output if there is any
                    if current_agent and agent_buffer.strip():
                        status.stop()
                        color = "yellow" if current_agent == "MarketAnalyst" else "magenta" if current_agent == "RiskManager" else "green"
                        console.print(Panel(
                            agent_buffer.strip(),
                            title=f"{current_agent} Report",
                            border_style=color
                        ))
                        status.start()

                    current_agent = event.author
                    agent_buffer = ""
                    status.update(f"Running [bold]{current_agent}[/bold]...")

                # Check for errors in the event stream
                if event.error_message:
                    status.stop()
                    console.print(f"\n[bold red]Error during workflow execution: {event.error_message}[/bold red]\n")
                    if "API key" in event.error_message:
                        console.print("[yellow]Hint: Please set the GEMINI_API_KEY environment variable.[/yellow]\n")
                    sys.exit(1)

                # Append content if available
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            agent_buffer += part.text

            # Print the final agent's report
            if current_agent and agent_buffer.strip():
                status.stop()
                color = "yellow" if current_agent == "MarketAnalyst" else "magenta" if current_agent == "RiskManager" else "green"

                # Enforce security disclaimer on final PM output
                final_text = agent_buffer.strip()
                if current_agent == "PortfolioManager":
                    final_text = sanitize_and_format_output(final_text)

                console.print(Panel(
                    final_text,
                    title=f"{current_agent} Output",
                    border_style=color
                ))

        console.print("\n[bold green]Analysis complete.[/bold green]")

    except (RuntimeError, ConnectionError, OSError, KeyError, ValueError, WorkflowExecutionError) as e:
        console.print(f"\n[bold red]System Error: {type(e).__name__}: {e}[/bold red]")
        sys.exit(1)
