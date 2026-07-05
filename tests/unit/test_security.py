"""Unit tests for src.security — ticker sanitization, risk limits, disclaimer."""
from src.security import (
    sanitize_ticker,
    enforce_risk_limits,
    sanitize_and_format_output,
    RiskAssessment,
)
from src.exceptions import (
    TradingAgentError,
    MarketDataError,
    TickerNotFoundError,
    IndicatorComputationError,
    WorkflowExecutionError,
)


def test_ticker_sanitization_valid():
    assert sanitize_ticker("AAPL")[0]
    assert sanitize_ticker("googl")[0]
    assert sanitize_ticker("BRK-B")[0]


def test_ticker_sanitization_invalid():
    is_valid, _ = sanitize_ticker("AAPL; DROP TABLE STOCKS;")
    assert not is_valid
    is_valid, _ = sanitize_ticker("AAPL & rm -rf /")
    assert not is_valid
    is_valid, _ = sanitize_ticker("TOO_LONG_TICKER")
    assert not is_valid
    is_valid, _ = sanitize_ticker("")
    assert not is_valid


def test_risk_limits_returns_pydantic_model():
    res = enforce_risk_limits(proposed_size_pct=3.0, stop_loss_pct=5.0, rsi_value=50.0)
    assert isinstance(res, RiskAssessment)


def test_risk_limits_default_safe():
    res = enforce_risk_limits(proposed_size_pct=3.0, stop_loss_pct=5.0, rsi_value=50.0)
    assert res.approved is True
    assert res.requires_review is False
    assert res.adjusted_size_pct == 3.0


def test_risk_limits_max_position_truncation():
    res = enforce_risk_limits(proposed_size_pct=10.0, stop_loss_pct=5.0, rsi_value=50.0)
    assert res.approved is True
    assert res.adjusted_size_pct == 5.0
    assert any("exceeds maximum limit" in w for w in res.warnings)


def test_risk_limits_overbought_ceiling():
    res = enforce_risk_limits(proposed_size_pct=4.0, stop_loss_pct=5.0, rsi_value=75.0)
    assert res.approved is True
    assert res.adjusted_size_pct == 2.0
    assert any("RSI is overbought" in w for w in res.warnings)


def test_risk_limits_wide_stop_loss_rejected():
    res = enforce_risk_limits(proposed_size_pct=3.0, stop_loss_pct=15.0, rsi_value=50.0)
    assert res.approved is False
    assert res.requires_review is False


def test_risk_limits_narrow_stop_loss_requires_review():
    res = enforce_risk_limits(proposed_size_pct=3.0, stop_loss_pct=1.0, rsi_value=50.0)
    assert res.approved is True
    assert res.requires_review is True
    assert any("too narrow" in w for w in res.warnings)


def test_output_disclaimer_appended():
    formatted = sanitize_and_format_output("Recommended action is BUY.")
    assert "SECURITY WARNING & COMPLIANCE DISCLAIMER" in formatted


def test_output_disclaimer_not_duplicated():
    formatted = sanitize_and_format_output("Recommended action is BUY.")
    assert sanitize_and_format_output(formatted) == formatted


def test_exception_hierarchy():
    assert issubclass(MarketDataError, TradingAgentError)
    assert issubclass(TickerNotFoundError, MarketDataError)
    assert issubclass(IndicatorComputationError, MarketDataError)
    assert issubclass(WorkflowExecutionError, TradingAgentError)
    assert not issubclass(WorkflowExecutionError, MarketDataError)
