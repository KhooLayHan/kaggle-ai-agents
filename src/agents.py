import os
import sys
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.tools.mcp_tool import McpToolset
from mcp import StdioServerParameters

# Load environment variables (e.g. GEMINI_API_KEY)
load_dotenv()

# Determine paths for launching the MCP Server
current_dir = os.path.dirname(os.path.abspath(__file__))
mcp_server_path = os.path.join(current_dir, "mcp_server.py")

# Determine Python interpreter to run the MCP server
# Prefer the current virtual environment's python executable
venv_python = os.path.join(os.path.dirname(current_dir), ".venv", "bin", "python")
if not os.path.exists(venv_python):
    venv_python = sys.executable

# Expose the local MCP server as an McpToolset for the Analyst Agent
trading_mcp_toolset = McpToolset(
    connection_params=StdioServerParameters(
        command=venv_python,
        args=[mcp_server_path],
    )
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
        "Provide a structured Risk Assessment Report summarizing your findings."
    ),
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
        "and this is an AI advisory model)."
    ),
)
