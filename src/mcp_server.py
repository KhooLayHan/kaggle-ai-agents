import functools
import logging
import sys
from typing import Any, Callable

import yfinance as yf
from cachetools import TTLCache
from fastmcp import FastMCP
from pydantic import BaseModel, Field

from src.security import sanitize_ticker

# Setup logging to stderr so it doesn't interfere with stdio JSON-RPC transport
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_trading_server")

# Initialize FastMCP Server
mcp = FastMCP("Market Trading MCP Server")

# TTL caches: price 5 min, indicators 1 hour, news 30 min. Only successful
# results are cached so transient errors don't poison subsequent calls.
_PRICE_CACHE: TTLCache = TTLCache(maxsize=128, ttl=300)
_INDICATORS_CACHE: TTLCache = TTLCache(maxsize=128, ttl=3600)
_NEWS_CACHE: TTLCache = TTLCache(maxsize=128, ttl=1800)


class StockPrice(BaseModel):
    """Live price statistics for a stock ticker."""
    ticker: str
    status: str
    current_price: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    volume: int | None = None
    currency: str = "USD"
    error: str | None = None


class TechnicalIndicators(BaseModel):
    """Technical analysis indicators (SMA, RSI, MACD) for a stock ticker."""
    ticker: str
    status: str
    latest_close: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    error: str | None = None


class NewsItem(BaseModel):
    """A single news headline for a stock ticker."""
    title: str | None = None
    publisher: str | None = None
    link: str | None = None
    type: str | None = None
    uuid: str | None = None


class NewsResponse(BaseModel):
    """News headlines response for a stock ticker."""
    ticker: str
    status: str
    items: list[NewsItem] = Field(default_factory=list)
    warning: str | None = None
    error: str | None = None


def _cached(cache: TTLCache, key_fn: Callable[..., tuple]) -> Callable:
    """Decorator: cache successful tool results under a TTLCache."""
    def deco(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            key = key_fn(*args, **kwargs)
            if key in cache:
                return cache[key]
            result = fn(*args, **kwargs)
            if getattr(result, "status", None) == "success":
                cache[key] = result
            return result
        return wrapper
    return deco


@mcp.tool()
@_cached(_PRICE_CACHE, lambda t: (t,))
def get_stock_price(ticker: str) -> StockPrice:
    """
    Fetch the latest market price, high, low, open, volume, and currency
    for a given stock ticker symbol.

    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'TSLA').

    Returns:
        A StockPrice model with live price statistics or error information.
    """
    logger.info("Fetching stock price for: %s", ticker)
    is_valid, ticker_clean = sanitize_ticker(ticker)
    if not is_valid:
        return StockPrice(ticker=ticker, status="rejected", error=f"Invalid ticker: {ticker!r}")
    try:
        t = yf.Ticker(ticker_clean)
        info = t.info

        # Extract relevant fields fallback chain
        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        if current_price is None:
            # Try to get it from history
            hist = t.history(period="1d")
            if not hist.empty:
                current_price = float(hist["Close"].iloc[-1])
                open_price = float(hist["Open"].iloc[-1])
                high_price = float(hist["High"].iloc[-1])
                low_price = float(hist["Low"].iloc[-1])
                volume = int(hist["Volume"].iloc[-1])
            else:
                return StockPrice(
                    ticker=ticker_clean,
                    status="failed",
                    error=f"Could not retrieve price for ticker: {ticker_clean}",
                )
        else:
            open_price = info.get("open") or info.get("regularMarketOpen")
            high_price = info.get("dayHigh") or info.get("regularMarketDayHigh")
            low_price = info.get("dayLow") or info.get("regularMarketDayLow")
            volume = info.get("volume") or info.get("regularMarketVolume")

        currency = info.get("currency", "USD")

        return StockPrice(
            ticker=ticker_clean,
            status="success",
            current_price=current_price,
            open=open_price,
            high=high_price,
            low=low_price,
            volume=volume,
            currency=currency,
        )
    except Exception as e:
        logger.error("Error fetching price for %s: %s", ticker_clean, e)
        return StockPrice(ticker=ticker_clean, status="failed", error=str(e))

@mcp.tool()
@_cached(_INDICATORS_CACHE, lambda t, p="3mo": (t, p))
def get_technical_indicators(ticker: str, period: str = "3mo") -> TechnicalIndicators:
    """
    Compute basic technical analysis indicators (SMA_20, SMA_50, RSI, MACD, MACD_Signal)
    for a stock ticker over a specified historical period.

    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'MSFT').
        period: Historical period to fetch ('1mo', '3mo', '6mo', '1y'). Default is '3mo'.

    Returns:
        A TechnicalIndicators model with the latest SMA, RSI, and MACD values.
    """
    logger.info("Computing technical indicators for: %s over %s", ticker, period)
    is_valid, ticker_clean = sanitize_ticker(ticker)
    if not is_valid:
        return TechnicalIndicators(
            ticker=ticker, status="rejected", error=f"Invalid ticker: {ticker!r}"
        )
    try:
        t = yf.Ticker(ticker_clean)
        # Fetch daily history
        hist = t.history(period=period, interval="1d")
        if hist.empty or len(hist) < 20:
            return TechnicalIndicators(
                ticker=ticker_clean,
                status="failed",
                error=f"Insufficient history (need at least 20 periods) for ticker: {ticker_clean}",
            )

        close_prices = hist["Close"]

        # Calculate SMAs
        sma_20 = float(close_prices.rolling(window=20).mean().iloc[-1])
        sma_50 = float(close_prices.rolling(window=50).mean().iloc[-1]) if len(close_prices) >= 50 else None

        # Calculate RSI (14-period)
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        rsi = float(100 - (100 / (1 + rs)).iloc[-1])

        # Calculate MACD (12, 26, 9)
        exp12 = close_prices.ewm(span=12, adjust=False).mean()
        exp26 = close_prices.ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        macd_signal = macd.ewm(span=9, adjust=False).mean()

        latest_macd = float(macd.iloc[-1])
        latest_signal = float(macd_signal.iloc[-1])
        latest_close = float(close_prices.iloc[-1])

        return TechnicalIndicators(
            ticker=ticker_clean,
            status="success",
            latest_close=latest_close,
            sma_20=sma_20,
            sma_50=sma_50,
            rsi_14=rsi,
            macd=latest_macd,
            macd_signal=latest_signal,
        )
    except Exception as e:
        logger.error("Error computing indicators for %s: %s", ticker_clean, e)
        return TechnicalIndicators(ticker=ticker_clean, status="failed", error=str(e))

@mcp.tool()
@_cached(_NEWS_CACHE, lambda t: (t,))
def get_stock_news(ticker: str) -> NewsResponse:
    """
    Retrieve the most recent news articles and sentiment headlines
    for a specified stock ticker.

    Args:
        ticker: The stock ticker symbol.

    Returns:
        A NewsResponse model with a list of news items (title, publisher, link, type).
    """
    logger.info("Fetching news for ticker: %s", ticker)
    is_valid, ticker_clean = sanitize_ticker(ticker)
    if not is_valid:
        return NewsResponse(
            ticker=ticker, status="rejected", error=f"Invalid ticker: {ticker!r}"
        )
    try:
        t = yf.Ticker(ticker_clean)
        raw_news = t.news
        if not raw_news:
            return NewsResponse(
                ticker=ticker_clean,
                status="no_news",
                warning=f"No recent news found for: {ticker_clean}",
            )

        news_items = [
            NewsItem(
                title=item.get("title"),
                publisher=item.get("publisher"),
                link=item.get("link"),
                type=item.get("type"),
                uuid=item.get("uuid"),
            )
            for item in raw_news[:5]
        ]
        return NewsResponse(ticker=ticker_clean, status="success", items=news_items)
    except Exception as e:
        logger.error("Error fetching news for %s: %s", ticker_clean, e)
        return NewsResponse(ticker=ticker_clean, status="failed", error=str(e))

if __name__ == "__main__":
    # Run server via stdio transport
    mcp.run(transport="stdio")
