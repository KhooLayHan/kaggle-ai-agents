# AI Stock Trading & Market Analysis Agent System

A modular, production-grade AI Agent system developed for the **Kaggle AI Agents Capstone Project (Agents for Business / Concierge Agents Track)**. The system coordinates specialized agents to analyze markets, apply risk parameters, and simulate portfolio decisions, utilizing the Google Agent Development Kit (ADK) and Model Context Protocol (MCP).

---

## Key Features

1. **Multi-Agent Architecture (Google ADK)**:
   - **Market Analyst Agent**: Fetches historical close prices, intraday metrics, technical indicators, and headlines, then outputs a Market Analysis Report.
   - **Risk Manager Agent**: Validates metrics, sets stop-loss/take-profit, assigns risk ratings, and approves/rejects compliance status.
   - **Portfolio Manager Agent**: Aggregates analyst and risk reviews to formulate the final decision (BUY/SELL/HOLD), transaction sizing, and disclaimers.
2. **Standardized Model Context Protocol (MCP)**:
   - Built on `fastmcp` to expose live tools for pricing, indicators, and headlines via stdio transport.
3. **Security Guardrails**:
   - Strictly limits transaction sizes to 5% max.
   - Restricts sizing to 2% max for overbought conditions (RSI > 70).
   - Validates symbol inputs to prevent prompt injection or execution escapes.
4. **Antigravity Integration**:
   - Integrates custom workspace rules (`.agents/AGENTS.md`) and registering skills (`.agents/skills/trading_assistant/SKILL.md`) for the Antigravity TUI/IDE.
5. **Interactive Console CLI**:
   - Outputs colorized, readable reports in the terminal.

---

## Installation & Setup

1. **Clone & Bootstrap**:
   Bootstrap the virtual environment and dependencies using `uv`:

   ```bash
   chmod +x setup.sh
   ./setup.sh
   source .venv/bin/activate
   ```

2. **Configure API Key**:
   Create a `.env` file in the project root:

   ```env
   GEMINI_API_KEY="your-gemini-api-key-here"
   ```

---

## Usage

### 1. Run via ADK CLI (Recommended)

The Google ADK CLI auto-discovers `agents/trading_agent/agent.py`, which exports
`root_agent` (the trading `Workflow`). This is the primary way to run the system.

```bash
source .venv/bin/activate

# Browser playground — select the "trading_agent" agent to see the workflow graph
adk web

# Headless interactive session
adk run trading_agent
```

When prompted, ask e.g. *"Analyze the stock symbol: AAPL."* The Market Analyst
retrieves live data via MCP tools, the Risk Manager validates sizing via the
`enforce_risk_limits` tool, and the Portfolio Manager emits a BUY/SELL/HOLD
decision with the mandatory compliance disclaimer.

**Security guardrails on the ADK path** are enforced programmatically:

- Invalid tickers are blocked before the model runs (`before_model_callback`).
- The compliance disclaimer is appended after the Portfolio Manager responds
  (`after_model_callback`).
- Position sizing is bounded by the `enforce_risk_limits` tool.

### 2. Interactive Trading CLI (Legacy)

Analyzes any stock ticker via a colorized terminal interface with its own
pre/post guardrails (defense in depth with the ADK callbacks):

```bash
python src/cli.py --ticker GOOGL
```

### 3. Run the MCP Server Standalone

Launch the MCP server in `stdio` mode to plug into custom clients (like Claude
Desktop or the Antigravity TUI):

```bash
python src/mcp_server.py
```

### 4. Running via Docker (Alternative)

Build and run the agent system inside a secure, containerized sandbox:

```bash
# Build the image
docker build -t trading-agent .

# Run market analysis
docker run --env GEMINI_API_KEY="your_api_key" trading-agent --ticker TSLA
```

---

## Conventions & Security

See `CONTEXT.md` for the full secure-coding standards, guardrail enforcement
map, and file map. `AGENTS.md` lists the mandatory behavioral rules for any
agent operating in this workspace.

### Quick commands

```bash
make test          # unit tests (offline, no network)
make test-integration  # live yfinance calls
make lint          # ruff check
make web           # adk web playground
make run           # adk run trading_agent
```

---

## Architecture Diagram

```mermaid
graph TD
    User([User Query]) -->|1. Request Ticker| CLI[CLI / Client]
    CLI -->|2. Sanitize & Validate| Sec[Security Guardrails]
    Sec -->|3. Trigger Workflow| ADK[ADK Workflow Engine]
    ADK -->|4. Query Data| Analyst[Market Analyst Agent]
    Analyst -->|5. Tools Request| MCP[MCP Server]
    MCP -->|6. Fetch live| API[(yfinance / Yahoo Finance)]
    Analyst -->|7. Analysis Report| Risk[Risk Manager Agent]
    Risk -->|8. Sizing & Stop-Loss| PM[Portfolio Manager Agent]
    PM -->|9. Final Trade Order| CLI
```
