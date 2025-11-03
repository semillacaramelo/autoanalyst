"""Asset Classification System

Detects asset class from symbol patterns to route data fetching and
apply appropriate trading strategy parameters.

Usage:
    from src.utils.asset_classifier import AssetClassifier

    info = AssetClassifier.classify("AAPL")
    # Returns: {"type": "US_EQUITY", "client_type": "stock", ...}

    info = AssetClassifier.classify("BTC/USD")
    # Returns: {"type": "CRYPTO", "client_type": "crypto", ...}
"""

import re
from typing import Dict


class AssetClassifier:
    """Detects asset class from symbol patterns."""

    # Asset class definitions with patterns and metadata
    # Order matters: check FOREX before CRYPTO to avoid USD pair confusion
    ASSET_CLASSES = {
        "FOREX": {
            "patterns": [
                # Forex with slash: must have non-USD base OR non-USD quote (but not both USD/USDT)
                r"^(EUR|GBP|AUD|NZD|CAD|CHF|SEK|NOK|DKK|TRY|ZAR)\/(USD|EUR|GBP|JPY|AUD|NZD|CAD|CHF)$",
                r"^USD\/(JPY|CHF|CAD|CNY|INR|MXN|RUB|BRL)$",  # USD as base
                # Forex without slash: 6 characters, not ending in USDT
                r"^(EUR|GBP|AUD|NZD|CAD|CHF|SEK|NOK)(USD|EUR|GBP|JPY|AUD|NZD|CAD|CHF)$",
                r"^USD(JPY|CHF|CAD|CNY|INR|MXN|RUB|BRL)$",
            ],
            "client_type": "forex",
            "markets": ["FOREX"],
            "trading_hours": "23/5",
            "description": "Foreign exchange pairs (23 hours, 5 days/week)",
        },
        "CRYPTO": {
            "patterns": [
                # Crypto: 3-5 letter base + /USD or /USDT or USD/USDT without slash
                r"^(BTC|ETH|SOL|ADA|DOT|MATIC|AVAX|LINK|UNI|ATOM|XRP|LTC|BCH|DOGE|SHIB|AAVE|ALGO|NEAR|FTM|SAND)\/(USD|USDT)$",
                r"^(BTC|ETH|SOL|ADA|DOT|MATIC|AVAX|LINK|UNI|ATOM|XRP|LTC|BCH|DOGE|SHIB|AAVE|ALGO|NEAR|FTM|SAND)(USD|USDT)$",
                # Generic 3-5 letter + USD/USDT (fallback for new coins)
                r"^[A-Z]{3,5}\/(USD|USDT)$",
                r"^[A-Z]{3,5}(USD|USDT)$",
            ],
            "client_type": "crypto",
            "markets": ["CRYPTO"],
            "trading_hours": "24/7",
            "description": "Cryptocurrency pairs traded 24/7",
        },
        "US_EQUITY": {
            "patterns": [
                r"^[A-Z]{1,5}$",  # AAPL, SPY, MSFT, GOOGL
            ],
            "client_type": "stock",
            "markets": ["US_EQUITY"],
            "trading_hours": "6.5h/day",
            "description": "US equity stocks (9:30-4:00 ET)",
        },
    }

    @classmethod
    def classify(cls, symbol: str) -> Dict[str, any]:
        """
        Detect asset class from symbol pattern.

        Args:
            symbol: Trading symbol to classify

        Returns:
            Dictionary with asset class information:
                - type: Asset class name (US_EQUITY, CRYPTO, FOREX)
                - client_type: Alpaca client type (stock, crypto, forex)
                - markets: List of markets where asset trades
                - trading_hours: Trading schedule description
                - description: Human-readable description
                - symbol: Original symbol (normalized)

        Examples:
            >>> AssetClassifier.classify("AAPL")
            {"type": "US_EQUITY", "client_type": "stock", ...}

            >>> AssetClassifier.classify("BTC/USD")
            {"type": "CRYPTO", "client_type": "crypto", ...}

            >>> AssetClassifier.classify("EUR/USD")
            {"type": "FOREX", "client_type": "forex", ...}

        Raises:
            ValueError: If symbol doesn't match any known pattern
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError(f"Invalid symbol: {symbol}")

        symbol = symbol.strip().upper()

        # Check forex patterns FIRST (before crypto to avoid EUR/USD → crypto misclassification)
        if cls._matches_asset_class(symbol, "FOREX"):
            return cls._build_result(symbol, "FOREX")

        # Check crypto patterns second
        if cls._matches_asset_class(symbol, "CRYPTO"):
            return cls._build_result(symbol, "CRYPTO")

        # Check equity patterns last (most common fallback)
        if cls._matches_asset_class(symbol, "US_EQUITY"):
            return cls._build_result(symbol, "US_EQUITY")

        # Unknown pattern
        raise ValueError(
            f"Unable to classify symbol '{symbol}'. "
            f"Supported formats: US stocks (AAPL), crypto (BTC/USD), forex (EUR/USD)"
        )

    @classmethod
    def _matches_asset_class(cls, symbol: str, asset_class: str) -> bool:
        """Check if symbol matches any pattern for given asset class."""
        patterns = cls.ASSET_CLASSES[asset_class]["patterns"]
        return any(re.match(pattern, symbol) for pattern in patterns)

    @classmethod
    def _build_result(cls, symbol: str, asset_class: str) -> Dict[str, any]:
        """Build classification result dictionary."""
        class_info = cls.ASSET_CLASSES[asset_class]
        return {
            "type": asset_class,
            "symbol": symbol,
            "client_type": class_info["client_type"],
            "markets": class_info["markets"],
            "trading_hours": class_info["trading_hours"],
            "description": class_info["description"],
        }

    @classmethod
    def is_crypto(cls, symbol: str) -> bool:
        """Quick check if symbol is cryptocurrency."""
        try:
            return cls.classify(symbol)["type"] == "CRYPTO"
        except ValueError:
            return False

    @classmethod
    def is_forex(cls, symbol: str) -> bool:
        """Quick check if symbol is forex pair."""
        try:
            return cls.classify(symbol)["type"] == "FOREX"
        except ValueError:
            return False

    @classmethod
    def is_equity(cls, symbol: str) -> bool:
        """Quick check if symbol is US equity."""
        try:
            return cls.classify(symbol)["type"] == "US_EQUITY"
        except ValueError:
            return False

    @classmethod
    def get_client_type(cls, symbol: str) -> str:
        """
        Get Alpaca client type for symbol.

        Returns: "stock", "crypto", or "forex"
        Raises: ValueError if symbol cannot be classified
        """
        return cls.classify(symbol)["client_type"]
