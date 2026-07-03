import unittest
from src.security import sanitize_ticker, enforce_risk_limits, sanitize_and_format_output
from src.mcp_server import get_stock_price, get_technical_indicators

class TestTradingAgentSystem(unittest.TestCase):
    
    def test_ticker_sanitization(self):
        # Valid tickers
        self.assertTrue(sanitize_ticker("AAPL")[0])
        self.assertTrue(sanitize_ticker("googl")[0])
        self.assertTrue(sanitize_ticker("BRK-B")[0])
        
        # Invalid tickers (SQL injections, shell scripts, formatting)
        self.assertFalse(sanitize_ticker("AAPL; DROP TABLE STOCKS;")[0])
        self.assertFalse(sanitize_ticker("AAPL & rm -rf /")[0])
        self.assertFalse(sanitize_ticker("TOO_LONG_TICKER")[0])
        self.assertFalse(sanitize_ticker("")[0])
        
    def test_risk_limits(self):
        # Test default safe parameters
        res = enforce_risk_limits(proposed_size_pct=3.0, stop_loss_pct=5.0, rsi_value=50.0)
        self.assertTrue(res["approved"])
        self.assertEqual(res["adjusted_size_pct"], 3.0)
        
        # Test max position size truncation (exceeds 5%)
        res = enforce_risk_limits(proposed_size_pct=10.0, stop_loss_pct=5.0, rsi_value=50.0)
        self.assertTrue(res["approved"])
        self.assertEqual(res["adjusted_size_pct"], 5.0)
        self.assertTrue(any("exceeds maximum limit" in w for w in res["warnings"]))
        
        # Test overbought condition restriction (RSI > 70 limits sizing to 2%)
        res = enforce_risk_limits(proposed_size_pct=4.0, stop_loss_pct=5.0, rsi_value=75.0)
        self.assertTrue(res["approved"])
        self.assertEqual(res["adjusted_size_pct"], 2.0)
        self.assertTrue(any("RSI is overbought" in w for w in res["warnings"]))
        
        # Test wide stop loss rejection (>12%)
        res = enforce_risk_limits(proposed_size_pct=3.0, stop_loss_pct=15.0, rsi_value=50.0)
        self.assertFalse(res["approved"])
        
    def test_output_disclaimer(self):
        txt = "Recommended action is BUY."
        formatted = sanitize_and_format_output(txt)
        self.assertIn("SECURITY WARNING & COMPLIANCE DISCLAIMER", formatted)
        
        # If disclaimer already exists, it shouldn't be duplicated
        self.assertEqual(sanitize_and_format_output(formatted), formatted)
        
    def test_mcp_tools(self):
        # Fetching price for a valid ticker should succeed
        res = get_stock_price("AAPL")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["ticker"], "AAPL")
        self.assertIn("current_price", res)
        
        # Technical indicators computation should succeed
        res = get_technical_indicators("AAPL")
        self.assertEqual(res["status"], "success")
        self.assertIn("rsi_14", res)

if __name__ == "__main__":
    unittest.main()
