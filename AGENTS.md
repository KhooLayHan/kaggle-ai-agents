# Trading Agent System Workspace Rules

This file outlines the behavior rules, architectural patterns, and security constraints that agents operating in this workspace must follow.

## Security Constraints

1. **Financial Sizing Safety**:
   - Any financial trade suggestions must never exceed a **5% allocation limit** per ticker.
   - Any recommendation that fails to include safety bounds (e.g. stop-loss) is strictly prohibited.
2. **Input Sanitization**:
   - All ticker queries must be sanitized via the python function `src/security.py:sanitize_ticker` to prevent injection attacks or shell escapes.
3. **Information Disclosure & Disclaimers**:
   - Agents must append the compliance disclaimer warning `src/security.py:REQUIRED_DISCLAIMER` to all investment suggestions.

## Code Guidelines

1. **Framework Usage**:
   - Use Google ADK (`google-adk`) for multi-agent workflows and task orchestration.
   - Expose tools through Model Context Protocol (MCP) using `fastmcp`.
2. **Environment & Sandbox**:
   - Keep credentials (e.g. `GEMINI_API_KEY`) secure. Do not hardcode secrets. Always read from environment variables or load using `.env` files.
