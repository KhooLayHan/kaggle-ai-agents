"""Unit tests for MCP tool input sanitization — no network, monkeypatched yfinance."""

from unittest.mock import MagicMock

import src.mcp_server as mcp_server
from src.mcp_server import NewsResponse, StockPrice


def _patch_yfinance(monkeypatch):
    """Replace yfinance.Ticker with a mock so no network calls happen."""
    mock_ticker = MagicMock()
    mock_ticker.info = {}
    mock_ticker.history.return_value.empty = True
    mock_ticker.news = []
    monkeypatch.setattr(mcp_server.yf, "Ticker", lambda _: mock_ticker)


def test_get_stock_price_rejects_injection(monkeypatch):
    _patch_yfinance(monkeypatch)
    res = mcp_server.get_stock_price("AAPL; DROP TABLE STOCKS;")
    assert isinstance(res, StockPrice)
    assert res.status == "rejected"
    assert "Invalid ticker" in (res.error or "")


def test_get_stock_price_rejects_shell_escape(monkeypatch):
    _patch_yfinance(monkeypatch)
    res = mcp_server.get_stock_price("AAPL & rm -rf /")
    assert res.status == "rejected"


def test_get_stock_price_rejects_empty(monkeypatch):
    _patch_yfinance(monkeypatch)
    res = mcp_server.get_stock_price("")
    assert res.status == "rejected"


def test_get_technical_indicators_rejects_injection(monkeypatch):
    _patch_yfinance(monkeypatch)
    res = mcp_server.get_technical_indicators("AAPL; DROP TABLE")
    assert res.status == "rejected"


def test_get_stock_news_rejects_injection(monkeypatch):
    _patch_yfinance(monkeypatch)
    res = mcp_server.get_stock_news("AAPL; DROP TABLE")
    assert isinstance(res, NewsResponse)
    assert res.status == "rejected"


def test_get_stock_price_caches_success(monkeypatch):
    """Second call for the same ticker should be served from cache (no yfinance)."""
    _patch_yfinance(monkeypatch)
    mcp_server._PRICE_CACHE[("AAPL",)] = StockPrice(
        ticker="AAPL",
        status="success",
        current_price=190.0,
        open=189.0,
        high=191.0,
        low=188.0,
        volume=1000000,
        currency="USD",
    )
    res = mcp_server.get_stock_price("AAPL")
    assert res.status == "success"
    assert res.current_price == 190.0
