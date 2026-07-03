# Hackathon Video Demonstration Recording Guide

Use this guide to record your ~5-minute project video. It is designed to walk you through presenting every single grading rubric requirement sequentially.

---

## 🎬 Video Flow Outline

### Part 1: Project Introduction & Track Selection (0:00 - 0:45)

1. **Visual**: Show your code editor (VS Code or Antigravity IDE) with the project structure and the `README.md`.
2. **Talk Track**:
   - Introduce yourself and your project: **"AI Agent Market Trading & Stock Analysis System"**.
   - State the track: **"Agents for Business"** (or **"Concierge Agents"**).
   - "With less than 3 days remaining before the deadline, we have successfully developed a fully production-grade, secure, multi-agent trading system utilizing Google's ADK and Model Context Protocol (MCP)."

### Part 2: Agent / Multi-Agent System (ADK) (0:45 - 1:45)

1. **Visual**: Open `src/agents.py` and `src/workflow.py` in your editor. Highlight the `market_analyst_agent`, `risk_manager_agent`, and `portfolio_manager_agent` definitions.
2. **Talk Track**:
   - "Here is the multi-agent system implemented using the official **Google ADK** (`google-adk`). We define three distinct agents:"
     - **MarketAnalyst**: responsible for fetching and evaluating stock data.
     - **RiskManager**: responsible for setting boundaries, stop-losses, and allocations.
     - **PortfolioManager**: responsible for making the final BUY/SELL/HOLD decision.
   - "In `workflow.py`, we construct a graph workflow (`edges=[("START", market_analyst_agent), ...]`) coordinating these agents sequentially."

### Part 3: MCP Server (1:45 - 2:30)

1. **Visual**: Open `src/mcp_server.py`. Highlight the `mcp = FastMCP(...)` and tools: `@mcp.tool() def get_stock_price(...)`, `@mcp.tool() def get_technical_indicators(...)`, etc.
2. **Talk Track**:
   - "To support live data, we built a standalone **MCP Server** using the `fastmcp` Python framework."
   - "The server runs over standard input/output (`stdio`) transport and exposes specialized tools to fetch real-time market data, news articles, and calculated technical indicators (like RSI and SMA) using Yahoo Finance."
   - "Our ADK Market Analyst Agent acts as an **MCP Client**, connecting to this server dynamically using `McpToolset`."

### Part 4: Security & Guardrails (2:30 - 3:15)

1. **Visual**: Open `src/security.py`. Point to the `sanitize_ticker`, `enforce_risk_limits`, and `sanitize_and_format_output` functions.
2. **Talk Track**:
   - "Security is a first-class citizen in this application. We have built strict security features:"
     - **Input Sanitization**: Rejects any input that isn't a valid ticker symbol, protecting against prompt injection and shell escape attacks.
     - **Financial Risk Limits**: Limits single-position allocation to 5%, drops it to 2% if the RSI indicator is overbought (RSI > 70), and enforces a maximum stop-loss window.
     - **Compliance Disclaimers**: Post-processes output to automatically append a professional security and risk warning disclaimer."

### Part 5: Antigravity Workspace Integration (3:15 - 4:00)

1. **Visual**: Open `.agents/AGENTS.md` and `.agents/skills/trading_assistant/SKILL.md`. Show the Antigravity TUI running in the terminal by typing `agy` (if installed) or reference the CLI panels.
2. **Talk Track**:
   - "Our project is integrated with **Google Antigravity**."
   - "We define project rules in `.agents/AGENTS.md` to guide AI agents coding in this directory, and we register a custom skill in `.agents/skills/trading_assistant/SKILL.md`."
   - "This allows the agent in the Antigravity TUI (`agy`) or IDE sidebar to automatically discover our stock analysis tools and execute our trading workflow."

### Part 6: CLI & Deployability Live Demo (4:00 - 5:00)

1. **Visual**: Open the terminal. Run the setup script and start the CLI:

   ```bash
   source .venv/bin/activate
   python src/cli.py --ticker GOOGL
   ```

   Show the output reports printing live in the terminal.
2. **Visual**: Show the `Dockerfile` and build/run commands.
3. **Talk Track**:
   - "For deployability, we have a `setup.sh` script to automate package management, and a `Dockerfile` that packages everything into a secure, containerized sandbox."
   - "Let's run a live analysis for Google stock (`GOOGL`)."
   - *(Point to the terminal output)*: "As you can see, the CLI runs our ADK workflow. First, the Market Analyst fetches the metrics, RSI, and news. Next, the Risk Manager calculates the stop-loss and approves the trade. Finally, the Portfolio Manager issues the BUY decision, accompanied by the required safety warnings."
   - "This wraps up our AI Agent Market Trading system presentation. Thank you!"

---

## 💡 Recording Tips

- **Resolution**: Record in 1080p and fullscreen your editor/terminal for readability.
- **Microphone**: Use a good headset microphone and record in a quiet room.
- **Preparation**: Pre-run the CLI command once to make sure `yfinance` fetches successfully before recording, and ensure `GEMINI_API_KEY` is set in the terminal you use.
