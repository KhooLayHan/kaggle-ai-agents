# Trading Agent System Workspace Rules

Mandatory behavioral rules for any agent operating in this workspace.
For the full secure-coding standards, guardrail enforcement map, and file
map, see `CONTEXT.md`.

## Setup

- Python **3.13**, managed with `uv`. Bootstrap: `./setup.sh` then `source .venv/bin/activate`.
- Add a dependency only by updating `pyproject.toml` and running `uv pip install -e .` (refreshes `uv.lock`).
- Load `GEMINI_API_KEY` from `.env` via `python-dotenv`. Never hardcode secrets; `.env` is gitignored.

## Commands

| Command | Purpose |
| --- | --- |
| `make web` / `adk web src/agents` | Browser playground — primary run path (select `trading_agent`). |
| `make run` / `adk run src/agents/trading_agent` | Headless interactive session. |
| `python main.py --ticker AAPL` | Legacy rich-console CLI (dispatcher; `python main.py` alone prints help). |
| `python src/mcp_server.py` | Run the MCP server standalone over stdio. |
| `make test` / `pytest` | **Unit tests only** — `pyproject.toml` sets `addopts = "-m 'not integration'"`. |
| `make test-integration` / `pytest -m integration` | Live yfinance network calls. |
| `make lint` / `ruff check src/ tests/ main.py` | Lint (note: there is no root `agents/` dir). |
| `make format` / `ruff format src/ tests/ main.py` | Format. |

Verify in this order: `make lint` -> `make test`.

## Architecture invariants

- **Agent discovery contract:** `src/agents/<name>/agent.py` must export `root_agent` (a `BaseAgent` or `Workflow`/`BaseNode`). The ADK CLI auto-discovers it. Do not relocate the agent definition.
- **Single canonical module:** `src/agents/trading_agent/agent.py` is the **only** definition of the three agents, the workflow, callbacks, and the risk tool. `src/workflow.py` is a thin re-export for the legacy CLI path — do not duplicate agent definitions across files.
- **MCP:** tools are exposed via `fastmcp` over stdio (`src/mcp_server.py`). The Market Analyst mounts them through an `McpToolset` with `StdioServerParameters`. The Risk Manager does **not** call MCP tools directly — it receives RSI from the analyst's report, preserving agent separation.
- **Dual-layer guardrails:** enforcement exists at **two** layers — ADK callbacks (`adk` CLI path) and `src/cli.py` pre/post-processing (legacy CLI path). Both must stay functional. Do not remove one layer because the other exists. Agent instructions are advisory; callbacks and tools are authoritative.

## Security constraints (mandatory)

1. **Input sanitization:** every ticker passes through `src/security.py:sanitize_ticker` before reaching a model or MCP tool. Rejects non-letters, oversized symbols, and injection payloads; normalizes to uppercase.
2. **Financial sizing safety:**
   - Hard cap **5% max allocation** per ticker.
   - Overbought ceiling **2% max** when RSI > 70.
   - Stop-loss band **1.5%–12%** below entry; outside this band is unsafe.
   - Sizing is enforced by the `enforce_risk_limits` tool the Risk Manager MUST call; recommendations without safety bounds are prohibited.
3. **Information disclosure:** every investment suggestion ends with `src/security.py:REQUIRED_DISCLAIMER`, appended programmatically (callback / CLI post-processor), not left to model compliance.

## Workflow rules

- Use Google ADK (`google-adk`) for multi-agent orchestration; expose tools via MCP using `fastmcp`.
- Workflow order is fixed: `market_analyst_agent` -> `risk_manager_agent` -> `portfolio_manager_agent` (sequential graph edges from `START`).
- Negative security test: in `adk run`, send `Analyze AAPL; DROP TABLE STOCKS` — the `before_model_callback` must block it with no model or MCP call.
