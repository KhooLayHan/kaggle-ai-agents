import logging
import sys
from typing import Dict, Any, List
import pandas as pd
import yfinance as yf
from fastmcp import FastMCP

# Setup logging to stderr so it doesn't interfere with stdio JSON-RPC transport
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_trading_server")

# Initialize FastMCP Server
mcp = FastMCP("Market Trading MCP Server")

@mcp.tool()
def get_stock_price(ticker: str) -> Dict[str, Any]:
    """
    Fetch the latest market price, high, low, open, volume, and currency
    for a given stock ticker symbol.
    
    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'TSLA').
        
    Returns:
        A dictionary containing live price statistics or error information.
    """
    logger.info(f"Fetching stock price for: {ticker}")
    ticker_clean = ticker.strip().upper()
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
                return {"error": f"Could not retrieve price for ticker: {ticker_clean}"}
        else:
            open_price = info.get("open") or info.get("regularMarketOpen")
            high_price = info.get("dayHigh") or info.get("regularMarketDayHigh")
            low_price = info.get("dayLow") or info.get("regularMarketDayLow")
            volume = info.get("volume") or info.get("regularMarketVolume")
            
        currency = info.get("currency", "USD")
        
        return {
            "ticker": ticker_clean,
            "current_price": current_price,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "volume": volume,
            "currency": currency,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error fetching price for {ticker_clean}: {e}")
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def get_technical_indicators(ticker: str, period: str = "3mo") -> Dict[str, Any]:
    """
    Compute basic technical analysis indicators (SMA_20, SMA_50, RSI, MACD, MACD_Signal)
    for a stock ticker over a specified historical period.
    
    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'MSFT').
        period: Historical period to fetch ('1mo', '3mo', '6mo', '1y'). Default is '3mo'.
        
    Returns:
        A dictionary with the latest calculated values for SMA_20, SMA_50, RSI, MACD, and Signal.
    """
    logger.info(f"Computing technical indicators for: {ticker} over {period}")
    ticker_clean = ticker.strip().upper()
    try:
        t = yf.Ticker(ticker_clean)
        # Fetch daily history
        hist = t.history(period=period, interval="1d")
        if hist.empty or len(hist) < 20:
            return {"error": f"Insufficient history (need at least 20 periods) for ticker: {ticker_clean}"}
            
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
        
        return {
            "ticker": ticker_clean,
            "latest_close": latest_close,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "rsi_14": rsi,
            "macd": latest_macd,
            "macd_signal": latest_signal,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error computing indicators for {ticker_clean}: {e}")
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def get_stock_news(ticker: str) -> List[Dict[str, Any]]:
    """
    Retrieve the most recent news articles and sentiment headlines
    for a specified stock ticker.
    
    Args:
        ticker: The stock ticker symbol.
        
    Returns:
        A list of dictionaries representing news items (title, publisher, link, publish time).
    """
    logger.info(f"Fetching news for ticker: {ticker}")
    ticker_clean = ticker.strip().upper()
    try:
        t = yf.Ticker(ticker_clean)
        raw_news = t.news
        if not raw_news:
            return [{"warning": f"No recent news found for: {ticker_clean}"}]
            
        news_items = []
        for item in raw_news[:5]: # Return top 5 items
            news_items.append({
                "title": item.get("title"),
                "publisher": item.get("publisher"),
                "link": item.get("link"),
                "type": item.get("type"),
                "uuid": item.get("uuid")
            })
        return news_items
    except Exception as e:
        logger.error(f"Error fetching news for {ticker_clean}: {e}")
        return [{"error": str(e)}]

if __name__ == "__main__":
    # Run server via stdio transport
    mcp.run(transport="stdio")
