"""
Re-export the canonical agent definitions from `agents.trading_agent.agent`.

The single source of truth lives at agents/trading_agent/agent.py so that the
`adk web` / `adk run` CLI auto-discovers `root_agent`. This shim preserves the
legacy `src.agents` import path used by src/cli.py and src/test_system.py.
"""
from agents.trading_agent.agent import (  # noqa: F401
    market_analyst_agent,
    risk_manager_agent,
    portfolio_manager_agent,
    trading_mcp_toolset,
)
