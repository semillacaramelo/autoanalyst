"""Unit tests for Asset Classification System

Tests 50+ symbol patterns across US equities, crypto, and forex.
"""

import pytest
from src.utils.asset_classifier import AssetClassifier


class TestAssetClassifier:
    """Test suite for AssetClassifier."""
    
    # US Equity Test Cases
    US_EQUITY_SYMBOLS = [
        "AAPL", "SPY", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA",
        "JPM", "V", "JNJ", "WMT", "PG", "MA", "UNH", "HD", "BAC", "XOM",
        "A", "BB", "C", "D", "F", "GM", "T", "VZ"  # 1-2 letter symbols
    ]
    
    # Crypto Test Cases (with slash)
    CRYPTO_SLASH_SYMBOLS = [
        "BTC/USD", "ETH/USD", "SOL/USD", "ADA/USD", "DOT/USD",
        "MATIC/USD", "AVAX/USD", "LINK/USD", "UNI/USD", "ATOM/USD",
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT"
    ]
    
    # Crypto Test Cases (no slash)
    CRYPTO_NO_SLASH_SYMBOLS = [
        "BTCUSD", "ETHUSD", "SOLUSD", "ADAUSD", "DOTUSD",
        "MATICUSD", "AVAXUSD", "LINKUSD", "UNIUSD", "ATOMUSD",
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT"
    ]
    
    # Forex Test Cases (with slash)
    FOREX_SLASH_SYMBOLS = [
        "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD",
        "NZD/USD", "EUR/GBP", "GBP/JPY", "EUR/JPY", "AUD/JPY"
    ]
    
    # Forex Test Cases (no slash)
    FOREX_NO_SLASH_SYMBOLS = [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
        "NZDUSD", "EURGBP", "GBPJPY", "EURJPY", "AUDJPY"
    ]
    
    # Invalid symbols
    INVALID_SYMBOLS = [
        "", "   ", "123", "TOOLONG", "A1B2C3",
        "BTC-USD", "BTC_USD", "?AAPL", "AAPL!", "A/B", "@#$%"
    ]
    
    def test_us_equity_classification(self):
        """Test US equity symbol classification."""
        for symbol in self.US_EQUITY_SYMBOLS:
            result = AssetClassifier.classify(symbol)
            assert result["type"] == "US_EQUITY", f"Failed for {symbol}"
            assert result["client_type"] == "stock"
            assert result["markets"] == ["US_EQUITY"]
            assert result["trading_hours"] == "6.5h/day"
            assert result["symbol"] == symbol.upper()
    
    def test_crypto_slash_classification(self):
        """Test crypto symbols with slash (BTC/USD format)."""
        for symbol in self.CRYPTO_SLASH_SYMBOLS:
            result = AssetClassifier.classify(symbol)
            assert result["type"] == "CRYPTO", f"Failed for {symbol}"
            assert result["client_type"] == "crypto"
            assert result["markets"] == ["CRYPTO"]
            assert result["trading_hours"] == "24/7"
            assert result["symbol"] == symbol.upper()
    
    def test_crypto_no_slash_classification(self):
        """Test crypto symbols without slash (BTCUSD format)."""
        for symbol in self.CRYPTO_NO_SLASH_SYMBOLS:
            result = AssetClassifier.classify(symbol)
            assert result["type"] == "CRYPTO", f"Failed for {symbol}"
            assert result["client_type"] == "crypto"
            assert result["markets"] == ["CRYPTO"]
            assert result["trading_hours"] == "24/7"
    
    def test_forex_slash_classification(self):
        """Test forex pairs with slash (EUR/USD format)."""
        for symbol in self.FOREX_SLASH_SYMBOLS:
            result = AssetClassifier.classify(symbol)
            assert result["type"] == "FOREX", f"Failed for {symbol}"
            assert result["client_type"] == "forex"
            assert result["markets"] == ["FOREX"]
            assert result["trading_hours"] == "23/5"
            assert result["symbol"] == symbol.upper()
    
    def test_forex_no_slash_classification(self):
        """Test forex pairs without slash (EURUSD format)."""
        for symbol in self.FOREX_NO_SLASH_SYMBOLS:
            result = AssetClassifier.classify(symbol)
            assert result["type"] == "FOREX", f"Failed for {symbol}"
            assert result["client_type"] == "forex"
            assert result["markets"] == ["FOREX"]
            assert result["trading_hours"] == "23/5"
    
    def test_invalid_symbols(self):
        """Test invalid symbols raise ValueError."""
        for symbol in self.INVALID_SYMBOLS:
            with pytest.raises(ValueError):
                AssetClassifier.classify(symbol)
    
    def test_case_insensitivity(self):
        """Test symbols are normalized to uppercase."""
        test_cases = [
            ("aapl", "US_EQUITY"),
            ("btc/usd", "CRYPTO"),
            ("eur/usd", "FOREX"),
            ("Msft", "US_EQUITY"),
            ("Eth/Usd", "CRYPTO")
        ]
        for symbol, expected_type in test_cases:
            result = AssetClassifier.classify(symbol)
            assert result["type"] == expected_type
            assert result["symbol"] == symbol.upper()
    
    def test_whitespace_handling(self):
        """Test symbols with leading/trailing whitespace."""
        test_cases = [
            ("  AAPL  ", "US_EQUITY"),
            (" BTC/USD ", "CRYPTO"),
            ("  EUR/USD  ", "FOREX")
        ]
        for symbol, expected_type in test_cases:
            result = AssetClassifier.classify(symbol)
            assert result["type"] == expected_type
            assert result["symbol"] == symbol.strip().upper()
    
    def test_helper_methods(self):
        """Test convenience helper methods."""
        # Test is_crypto
        assert AssetClassifier.is_crypto("BTC/USD") is True
        assert AssetClassifier.is_crypto("AAPL") is False
        assert AssetClassifier.is_crypto("EUR/USD") is False
        assert AssetClassifier.is_crypto("INVALID") is False
        
        # Test is_forex
        assert AssetClassifier.is_forex("EUR/USD") is True
        assert AssetClassifier.is_forex("AAPL") is False
        assert AssetClassifier.is_forex("BTC/USD") is False
        assert AssetClassifier.is_forex("INVALID") is False
        
        # Test is_equity
        assert AssetClassifier.is_equity("AAPL") is True
        assert AssetClassifier.is_equity("BTC/USD") is False
        assert AssetClassifier.is_equity("EUR/USD") is False
        assert AssetClassifier.is_equity("INVALID") is False
    
    def test_get_client_type(self):
        """Test get_client_type convenience method."""
        assert AssetClassifier.get_client_type("AAPL") == "stock"
        assert AssetClassifier.get_client_type("BTC/USD") == "crypto"
        assert AssetClassifier.get_client_type("EUR/USD") == "forex"
        
        with pytest.raises(ValueError):
            AssetClassifier.get_client_type("INVALID")
    
    def test_result_structure(self):
        """Test classification result has all required fields."""
        result = AssetClassifier.classify("AAPL")
        
        # Check all required fields present
        required_fields = ["type", "symbol", "client_type", "markets", 
                          "trading_hours", "description"]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
        
        # Check field types
        assert isinstance(result["type"], str)
        assert isinstance(result["symbol"], str)
        assert isinstance(result["client_type"], str)
        assert isinstance(result["markets"], list)
        assert isinstance(result["trading_hours"], str)
        assert isinstance(result["description"], str)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Single letter stock (valid)
        result = AssetClassifier.classify("A")
        assert result["type"] == "US_EQUITY"
        
        # 5-letter stock (maximum for US equity)
        result = AssetClassifier.classify("GOOGL")
        assert result["type"] == "US_EQUITY"
        
        # 3-letter crypto base (minimum)
        result = AssetClassifier.classify("BTC/USD")
        assert result["type"] == "CRYPTO"
        
        # 5-letter crypto base (maximum common)
        result = AssetClassifier.classify("MATIC/USD")
        assert result["type"] == "CRYPTO"
    
    def test_total_coverage(self):
        """Verify we test 50+ unique symbols as required."""
        all_symbols = (
            self.US_EQUITY_SYMBOLS +
            self.CRYPTO_SLASH_SYMBOLS +
            self.CRYPTO_NO_SLASH_SYMBOLS +
            self.FOREX_SLASH_SYMBOLS +
            self.FOREX_NO_SLASH_SYMBOLS
        )
        unique_symbols = set(all_symbols)
        assert len(unique_symbols) >= 50, \
            f"Only testing {len(unique_symbols)} symbols, need 50+"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
