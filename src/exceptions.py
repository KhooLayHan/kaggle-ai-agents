"""Custom exception hierarchy for the trading agent system."""

class TradingAgentError(Exception):
    """Base exception for all trading agent system errors."""

class MarketDataError(TradingAgentError):
    """Raised when market data retrieval or computation fails."""

class TickerNotFoundError(MarketDataError):
    """Raised when a ticker passes sanitization but has no data on the exchange."""

class IndicatorComputationError(MarketDataError):
    """Raised when technical indicator computation fails (insufficient data, numeric errors)."""

class WorkflowExecutionError(TradingAgentError):
    """Raised when the ADK multi-agent workflow fails during execution."""
