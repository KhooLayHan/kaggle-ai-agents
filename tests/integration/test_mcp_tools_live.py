"""Integration tests — live network calls to yfinance. Skipped by default."""

import pytest

from src.mcp_server import get_stock_price, get_technical_indicators


@pytest.mark.integration
def test_get_stock_price_live():
    res = get_stock_price("AAPL")
    assert res.status == "success"
    assert res.ticker == "AAPL"
    assert res.current_price is not None


@pytest.mark.integration
def test_get_technical_indicators_live():
    res = get_technical_indicators("AAPL")
    assert res.status == "success"
    assert res.rsi_14 is not None
