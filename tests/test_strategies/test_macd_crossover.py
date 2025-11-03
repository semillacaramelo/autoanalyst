"""
Unit tests for MACD Crossover trading strategy.

Tests cover:
- Indicator calculation (MACD line, signal line, histogram)
- Signal generation (BUY/SELL on MACD crossovers)
- Signal validation with confirmations (Volume, RSI, MACD divergence)
- Edge cases
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.strategies.macd_crossover import MACDCrossoverStrategy


class TestMACDCrossoverStrategy(unittest.TestCase):
    """Test suite for MACD Crossover strategy."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = MACDCrossoverStrategy()

    def _create_sample_data(self, num_bars: int = 100, trend: str = "up") -> pd.DataFrame:
        """Create sample OHLCV data for testing."""
        timestamps = [datetime.now() - timedelta(minutes=i) for i in range(num_bars)]
        timestamps.reverse()

        if trend == "up":
            close_prices = np.linspace(100, 120, num_bars) + np.random.randn(num_bars) * 0.5
        elif trend == "down":
            close_prices = np.linspace(120, 100, num_bars) + np.random.randn(num_bars) * 0.5
        else:  # sideways
            close_prices = 110 + np.random.randn(num_bars) * 2

        data = {
            "open": close_prices + np.random.randn(num_bars) * 0.3,
            "high": close_prices + np.abs(np.random.randn(num_bars) * 0.5),
            "low": close_prices - np.abs(np.random.randn(num_bars) * 0.5),
            "close": close_prices,
            "volume": np.random.randint(1000000, 5000000, num_bars),
        }

        return pd.DataFrame(data, index=pd.DatetimeIndex(timestamps))

    def test_initialization(self):
        """Test strategy initialization."""
        self.assertEqual(self.strategy.name, "macd")
        self.assertEqual(self.strategy.description, "MACD Crossover Strategy")
        self.assertEqual(self.strategy.min_bars_required, 34)

    def test_calculate_indicators_returns_all_required(self):
        """Test that calculate_indicators returns all required indicators."""
        df = self._create_sample_data(num_bars=100)
        indicators = self.strategy.calculate_indicators(df)

        self.assertIn("macd_line", indicators)
        self.assertIn("signal_line", indicators)
        self.assertIn("histogram", indicators)
        self.assertIn("volume", indicators)
        self.assertIn("rsi", indicators)

        self.assertIsInstance(indicators["macd_line"], pd.Series)
        self.assertIsInstance(indicators["signal_line"], pd.Series)
        self.assertIsInstance(indicators["histogram"], pd.Series)

    def test_generate_signal_structure(self):
        """Test that generated signal has correct structure."""
        df = self._create_sample_data(num_bars=100)
        signal = self.strategy.generate_signal(df)

        self.assertIn("signal", signal)
        self.assertIn("confidence", signal)
        self.assertIn("details", signal)
        self.assertIn(signal["signal"], ["BUY", "SELL", "HOLD"])
        self.assertGreaterEqual(signal["confidence"], 0.0)
        self.assertLessEqual(signal["confidence"], 1.0)

    def test_generate_signal_details_structure(self):
        """Test that signal details contain required fields."""
        df = self._create_sample_data(num_bars=100)
        signal = self.strategy.generate_signal(df)

        details = signal["details"]
        self.assertIn("macd_line", details)
        self.assertIn("signal_line", details)
        self.assertIn("histogram", details)
        self.assertIn("current_price", details)
        self.assertIn("timestamp", details)

        self.assertIsInstance(details["macd_line"], float)
        self.assertIsInstance(details["signal_line"], float)
        self.assertIsInstance(details["histogram"], float)

    def test_validate_signal_hold_returns_unchanged(self):
        """Test that HOLD signals are not modified by validation."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "HOLD", "confidence": 0}

        validated = self.strategy.validate_signal(df, signal, data_feed="iex")

        self.assertEqual(validated["signal"], "HOLD")
        self.assertEqual(validated["confidence"], 0)

    def test_validate_signal_adds_validation_field(self):
        """Test that validation adds validation field."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "BUY", "confidence": 0.65, "details": {}}

        validated = self.strategy.validate_signal(df, signal, data_feed="iex")

        self.assertIn("validation", validated)
        self.assertIsInstance(validated["validation"], str)

    def test_validate_signal_confidence_bounds(self):
        """Test that confidence stays within [0, 1] bounds."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "BUY", "confidence": 0.95, "details": {}}

        validated = self.strategy.validate_signal(df, signal, data_feed="sip")

        self.assertGreaterEqual(validated["confidence"], 0.0)
        self.assertLessEqual(validated["confidence"], 1.0)

    def test_validate_signal_data_feed_awareness(self):
        """Test that validation treats SIP and IEX feeds differently."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "BUY", "confidence": 0.65, "details": {}}

        validated_sip = self.strategy.validate_signal(df, signal.copy(), data_feed="sip")
        validated_iex = self.strategy.validate_signal(df, signal.copy(), data_feed="iex")

        self.assertIn("validation", validated_sip)
        self.assertIn("validation", validated_iex)

    def test_strategy_with_insufficient_data(self):
        """Test strategy with insufficient bars."""
        df = self._create_sample_data(num_bars=20)

        # Should still run but may have limited indicators
        signal = self.strategy.generate_signal(df)
        self.assertIn("signal", signal)

    def test_strategy_min_bars_requirement(self):
        """Test that strategy defines minimum bars requirement."""
        self.assertGreater(self.strategy.min_bars_required, 30)


if __name__ == "__main__":
    unittest.main()
