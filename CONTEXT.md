# Project Context — Secure Coding & Project Conventions

This document is the authoritative reference for agents and contributors working
in the `kaggle-ai-agents` workspace. It covers project conventions, secure-coding
standards, the guardrail enforcement map, run/test commands, and a file map.

For behavioral rules that any agent in this workspace MUST follow, see `AGENTS.md`.
This document expands on those rules with concrete enforcement points.

---

## 1. Project Conventions

### Tooling
- **Package manager:** `uv` (Python 3.13). Bootstrap with `./setup.sh`.
- **Primary run path:** the Google ADK CLI (`adk web`, `adk run`).
- **Agent discovery contract:** `agents/<name>/agent.py` must export `root_agent`
  as a `BaseAgent` or `BaseNode` (a `Workflow` is a `BaseNode`). The ADK CLI
  auto-discovers this. Do not relocate the agent definition.
- **MCP:** tools are exposed via `fastmcp` over stdio transport (`src/mcp_server.py`).
  The analyst agent mounts them through an `McpToolset` with `StdioServerParameters`.
- **Dependencies:** declared in `pyproject.toml`; pinned via `uv.lock`. Do not add
  a dependency without updating the lockfile (`uv pip install -e .`).

### Canonical source of truth
- `agents/trading_agent/agent.py` is the **single** definition of the three agents,
  the workflow, the callbacks, and the risk tool.
- `src/agents.py` and `src/workflow.py` are shims that re-import from the canonical
  module so the legacy `src/cli.py` path keeps working. Do not duplicate agent
  definitions across files.

### Secrets
- Load credentials (e.g. `GEMINI_API_KEY`) from `.env` via `python-dotenv`.
- **Never** hardcode secrets, API keys, or project IDs in source files.
- `.env` is gitignored; never commit it.

---

## 2. Secure Coding Standards

These standards are mandatory. Each has an enforcement point listed in section 3.

### Input sanitization
- Every ticker query must pass through `src.security.sanitize_ticker` before
  reaching a model or an MCP tool. The function rejects non-letter characters,
  overly long symbols, and shell/SQL-injection payloads.
- Tickers are normalized to uppercase before use.

### Financial sizing safety
- Hard cap: **5% max allocation** per ticker.
- Overbought ceiling: when RSI > 70, max sizing drops to **2%**.
- Stop-loss band: **1.5%–12%** below entry. Outside this band the position is
  flagged unsafe (too narrow → early-exit risk; too wide → unbounded loss).

### Information disclosure
- Every investment suggestion must end with `src.security.REQUIRED_DISCLAIMER`.
- The disclaimer is appended programmatically (callback / CLI post-processor),
  not left to model compliance alone.

### Defense in depth
- Guardrails are enforced at **two layers**: ADK callbacks (the `adk` CLI path)
  and `src/cli.py` pre/post-processing (the legacy CLI path). Both must remain
  functional. Do not remove one layer because the other exists.

---

## 3. Guardrail Enforcement Map

| Rule | ADK CLI path (`adk web`/`adk run`) | Legacy CLI path (`src/cli.py`) |
|------|-----------------------------------|--------------------------------|
| Ticker sanitization | `market_analyst_before_model` callback blocks invalid tickers before the model call | `sanitize_ticker` pre-check before workflow launch |
| 5% sizing cap / 2% overbought ceiling / stop-loss band | `enforce_risk_limits` tool the Risk Manager MUST call; instruction makes compliance status depend on `approved` and `requires_review` | Instruction-only (no programmatic enforcement in legacy path today) |
| Required disclaimer | `portfolio_manager_after_model` callback appends `REQUIRED_DISCLAIMER` | `sanitize_and_format_output` post-processing on PM output |

Notes:
- Agent instructions are **advisory**; callbacks and tools are **authoritative**.
- The `enforce_risk_limits` tool receives RSI extracted by the Risk Manager from
  the Market Analyst's report (Option A). The Risk Manager does not call the MCP
  tools directly, preserving agent separation.

---

## 4. Run & Test Commands

All commands assume `source .venv/bin/activate` first.

| Command | Purpose |
|---------|---------|
| `make web` or `adk web` | Browser playground (select `trading_agent`); renders the workflow graph |
| `make run` or `adk run trading_agent` | Headless interactive session against the workflow |
| `make test` or `pytest` | Unit tests (offline, no network) — sanitization, risk limits, disclaimer, MCP sanitization |
| `make test-integration` or `pytest -m integration` | Integration tests (live yfinance network calls) |
| `make lint` or `ruff check agents/ src/ tests/ main.py` | Lint all source + test files |
| `python main.py` | Print help and available commands |
| `python main.py --ticker AAPL` | Legacy rich-console CLI via dispatcher |
| `python src/mcp_server.py` | Run the MCP server standalone over stdio |
| `docker build -t trading-agent . && docker run --env GEMINI_API_KEY=... trading-agent --ticker TSLA` | Containerized run (alternatives path) |

### Negative test (security)
- In `adk run trading_agent`, send: `Analyze AAPL; DROP TABLE STOCKS`
- Expected: the `before_model_callback` blocks the request and returns the
  security-refusal message. No model call, no MCP tool invocation.

---

## 5. File Map

| Path | Role |
|------|------|
| `agents/trading_agent/agent.py` | **Canonical**: 3 agents, workflow, callbacks, risk tool, `root_agent` |
| `agents/__init__.py`, `agents/trading_agent/__init__.py` | Package markers |
| `src/agents.py` | Shim re-exporting canonical agents (legacy import path) |
| `src/workflow.py` | Shim re-exporting canonical workflow + `run_trading_workflow()` |
| `src/cli.py` | Legacy rich-console CLI with its own guardrails |
| `src/mcp_server.py` | FastMCP server exposing price / indicators / news tools over stdio (sanitized + TTL-cached) |
| `src/security.py` | `sanitize_ticker`, `enforce_risk_limits`, `sanitize_and_format_output`, `REQUIRED_DISCLAIMER` |
| `tests/unit/test_security.py` | Unit tests: ticker sanitization, risk limits (incl. `requires_review`), disclaimer |
| `tests/unit/test_mcp_sanitization.py` | Unit tests: MCP tool input rejection + cache hit (no network) |
| `tests/integration/test_mcp_tools_live.py` | Integration tests: live yfinance calls (marked `@pytest.mark.integration`) |
| `tests/conftest.py` | Pytest config: sys.path bootstrap, marker registration |
| `main.py` | Entry point dispatcher (`--ticker`, `--web`, or help) |
| `Makefile` | Shortcuts: `make test`, `make lint`, `make web`, `make run` |
| `Dockerfile` | Containerized build for the legacy CLI |
| `setup.sh` | `uv` bootstrap script |
| `pyproject.toml` / `uv.lock` | Dependencies |
| `AGENTS.md` | Mandatory behavioral rules for workspace agents |
| `CONTEXT.md` | This file |
| `README.md` | User-facing documentation |
