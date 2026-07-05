"""Canonical agent definitions: 3-agent trading workflow with ADK callbacks and MCP toolset."""

import os
import re
import sys
from dotenv import load_dotenv
from google.adk import Agent, Workflow
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools.mcp_tool import McpToolset
from google.genai import types
from mcp import StdioServerParameters

from src.security import (  # noqa: E402
    sanitize_ticker,
    enforce_risk_limits,
    sanitize_and_format_output,
)

current_dir = os.path.dirname(os.path.abspath(__file__))
# Project root is three levels up: src/agents/trading_agent/ → project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables (e.g. GEMINI_API_KEY)
load_dotenv()

# Path to the MCP server launched as a subprocess for the Analyst Agent
mcp_server_path = os.path.join(project_root, "src", "mcp_server.py")

# Determine Python interpreter to run the MCP server
# Prefer the current virtual environment's python executable
venv_python = os.path.join(project_root, ".venv", "bin", "python")
if not os.path.exists(venv_python):
    venv_python = sys.executable

# Expose the local MCP server as an McpToolset for the Analyst Agent
trading_mcp_toolset = McpToolset(
    connection_params=StdioServerParameters(
        command=venv_python,
        args=[mcp_server_path],
    )
)

# Regex used to locate a candidate ticker token inside user messages.
_TICKER_PATTERN = re.compile(r"\b([A-Z]{1,5}(?:[.-][A-Z]{1,2})?)\b")
_SECURITY_REFUSAL = (
    "Request blocked by security guardrail: no valid stock ticker was found, "
    "or the supplied symbol failed sanitization. Please provide a 1-5 letter "
    "ticker symbol (optionally with a dot or hyphen, e.g. 'BRK-B')."
)


def _extract_ticker_from_contents(contents: list[types.Content]) -> str | None:
    """Scan the latest user message for a candidate ticker token."""
    for content in reversed(contents):
        if getattr(content, "role", None) != "user":
            continue
        if not content.parts:
            continue
        text = "".join(p.text for p in content.parts if getattr(p, "text", None))
        match = _TICKER_PATTERN.search(text)
        if match:
            return match.group(1)
    return None


def market_analyst_before_model(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmResponse | None:
    """
    Pre-model guardrail for the Market Analyst.

    Extracts a candidate ticker from the incoming user message, runs it through
    `src.security.sanitize_ticker`, and blocks the model call if it is invalid.
    This enforces the AGENTS.md input-sanitization rule on the `adk` CLI path
    (where `src/cli.py` guardrails do not run).
    """
    candidate = _extract_ticker_from_contents(llm_request.contents)
    if candidate is None:
        # No ticker-like token at all; let the model ask the user for one.
        return None
    is_valid, clean = sanitize_ticker(candidate)
    if not is_valid:
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text=_SECURITY_REFUSAL)],
            ),
        )
    # Valid: stash the normalized ticker in invocation state for downstream use
    callback_context.state["sanitized_ticker"] = clean
    return None


def portfolio_manager_after_model(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> LlmResponse | None:
    """
    Post-model guardrail for the Portfolio Manager.

    Guarantees `REQUIRED_DISCLAIMER` is appended to every trade-decision output,
    satisfying the AGENTS.md disclosure rule on the `adk` CLI path.
    """
    if not llm_response.content or not llm_response.content.parts:
        return None
    texts = [p.text for p in llm_response.content.parts if getattr(p, "text", None)]
    joined = "".join(texts)
    if not joined.strip():
        return None
    patched = sanitize_and_format_output(joined)
    if patched == joined:
        return None
    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[types.Part.from_text(text=patched)],
        ),
        usage_metadata=llm_response.usage_metadata,
        grounding_metadata=llm_response.grounding_metadata,
    )


# 1. Market Analyst Agent: retrieves market data and produces technical & sentiment analysis
market_analyst_agent = Agent(
    name="MarketAnalyst",
    model="gemini-2.5-flash",
    instruction=(
        "You are an expert financial analyst. Your task is to perform a detailed stock analysis. "
        "Use the tools provided in your toolset to retrieve stock price, technical indicators, and news "
        "for the user-specified stock ticker.\n\n"
        "Generate a structured Market Analysis Report containing:\n"
        "1. Current Market Metrics (latest close, open, high, low, volume).\n"
        "2. Technical Indicators Analysis (RSI value & meaning, SMA 20 vs SMA 50 comparison, MACD and signal).\n"
        "3. News Sentiment (summary of recent news headlines and general vibe).\n"
        "4. Price Trend Conclusion (Bullish, Bearish, or Neutral) and rationale."
    ),
    tools=[trading_mcp_toolset],
    before_model_callback=market_analyst_before_model,
)

# 2. Risk Manager Agent: assesses volatility, stops, sizing, and security guardrails
risk_manager_agent = Agent(
    name="RiskManager",
    model="gemini-2.5-flash",
    instruction=(
        "You are an expert risk manager. Your task is to review the Market Analyst's report and assess "
        "risk parameters. You must adhere to the following rules:\n"
        "- Max position sizing is 5% of the total portfolio.\n"
        "- High-risk stocks (e.g., RSI > 70 indicating overbought, or high price volatility) must have smaller sizing (1-2%).\n"
        "- Determine a clear Stop-Loss (e.g., 5-8% below current price) and Take-Profit (e.g., 15-20% above current price).\n"
        "- Assign a risk rating: LOW, MEDIUM, or HIGH.\n"
        "- Set a compliance status: APPROVED or REJECTED (REJECTED if indicators are extremely volatile or data is missing).\n\n"
        "MANDATORY: Before finalizing your Risk Assessment Report, you MUST call the "
        "`enforce_risk_limits` tool with your proposed sizing, stop-loss percentage, and the RSI value "
        "reported by the Market Analyst. Use the tool's returned `adjusted_size_pct` as your final "
        "sizing and include any warnings verbatim in your report. If the tool returns "
        "`approved: false`, your compliance status MUST be REJECTED. If the tool returns "
        "`requires_review: true`, you MUST downgrade the risk rating to at least MEDIUM and "
        "reduce your final sizing by 1%.\n\n"
        "Provide a structured Risk Assessment Report summarizing your findings."
    ),
    tools=[enforce_risk_limits],
)

# 3. Portfolio Manager Agent: makes final decision (BUY/SELL/HOLD) and aggregates details
portfolio_manager_agent = Agent(
    name="PortfolioManager",
    model="gemini-2.5-flash",
    instruction=(
        "You are a professional portfolio manager. Your task is to make the final trading decision: "
        "BUY, SELL, or HOLD.\n"
        "Review the reports from both the Market Analyst and the Risk Manager.\n\n"
        "Rules:\n"
        "1. If the Risk Manager's compliance status is 'REJECTED', you MUST execute a 'HOLD' decision.\n"
        "2. Synthesize their reports and write a clear, executive Trading Order Decision. Include:\n"
        "   - Decision: [BUY / SELL / HOLD]\n"
        "   - Ticker symbol analyzed\n"
        "   - Final sizing, Stop-Loss, and Take-Profit levels\n"
        "   - Core Rationale (combining trend direction and risk assessment)\n"
        "   - Security & Compliance Disclaimer (remind the user that trading involves risk, "
        "and this is an AI advisory model):\n"
        "     'This AI-generated analysis is for informational and educational purposes only. "
        "It does not constitute professional investment advice or a recommendation to buy or sell securities. "
        "Trading stocks and assets involves significant financial risk. Past performance is not indicative of "
        "future results. Always consult with a licensed financial advisor before making any investment decisions.'"
    ),
    after_model_callback=portfolio_manager_after_model,
)

# Define the ADK workflow graph coordinating the three specialized agents sequentially
trading_workflow = Workflow(
    name="TradingWorkflow",
    edges=[
        ("START", market_analyst_agent),
        (market_analyst_agent, risk_manager_agent),
        (risk_manager_agent, portfolio_manager_agent),
    ]
)

# Expose the workflow as the root_agent for Google ADK CLI tool
root_agent = trading_workflow
