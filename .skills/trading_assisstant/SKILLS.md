---
name: trading_assistant
description: Analyze stock tickers, retrieve live prices, compute indicators, and formulate trade orders using the multi-agent system.
---

# Trading Assistant Skill

This skill registers a custom AI stock market analysis and trading order generator in the Antigravity TUI or sidebar chat.

## Instructions

1. When the user asks to analyze a stock ticker (e.g. "analyze AAPL" or "what is the trend for TSLA?"):
   - Sanitize the ticker using `src/security.py:sanitize_ticker`.
   - Run the trading workflow using `src/workflow.py:run_trading_workflow` or directly call `src/cli.py` with `python src/cli.py --ticker <ticker>`.
   - Display the reports from the **Market Analyst**, **Risk Manager**, and **Portfolio Manager** step-by-step.
   - Ensure the final response contains the risk warnings and disclaimers.

## Example Prompts

- "Analyze MSFT stock and give me a buy/sell trade decision"
- "Retrieve technical indicators for NVDA and run risk checks"
