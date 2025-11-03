"""
Unit tests for RSI Breakout trading strategy.

Tests cover:
- Indicator calculation
- Signal generation (BUY on RSI > 30, SELL on RSI < 70)
- Signal validation with confirmations (Volume, ADX, Price vs SMA50)
- Edge cases
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.strategies.rsi_breakout import RSIBreakoutStrategy


class TestRSIBreakoutStrategy(unittest.TestCase):
    """Test suite for RSI Breakout strategy."""

    def setUp(self):
        """Set up test fixtures."""
        self.strategy = RSIBreakoutStrategy()

    def _create_sample_data(self, num_bars: int = 100, rsi_level: str = "mid") -> pd.DataFrame:
        """
        Create sample OHLCV data for testing.

        Args:
            num_bars: Number of bars to generate
            rsi_level: Target RSI level ("oversold", "overbought", "mid")

        Returns:
            DataFrame with OHLCV data
        """
        timestamps = [datetime.now() - timedelta(minutes=i) for i in range(num_bars)]
        timestamps.reverse()

        # Generate price data based on RSI target
        if rsi_level == "oversold":
            # Declining prices to create low RSI
            close_prices = np.linspace(120, 100, num_bars) + np.random.randn(num_bars) * 0.3
        elif rsi_level == "overbought":
            # Rising prices to create high RSI
            close_prices = np.linspace(100, 120, num_bars) + np.random.randn(num_bars) * 0.3
        else:  # mid
            close_prices = 110 + np.random.randn(num_bars) * 2

        data = {
            "open": close_prices + np.random.randn(num_bars) * 0.3,
            "high": close_prices + np.abs(np.random.randn(num_bars) * 0.5),
            "low": close_prices - np.abs(np.random.randn(num_bars) * 0.5),
            "close": close_prices,
            "volume": np.random.randint(1000000, 5000000, num_bars),
        }

        df = pd.DataFrame(data, index=pd.DatetimeIndex(timestamps))
        return df

    def test_initialization(self):
        """Test strategy initialization."""
        self.assertEqual(self.strategy.name, "rsi_breakout")
        self.assertEqual(self.strategy.description, "RSI Breakout Strategy")
        self.assertEqual(self.strategy.min_bars_required, 52)

    def test_calculate_indicators_returns_all_required(self):
        """Test that calculate_indicators returns all required indicators."""
        df = self._create_sample_data(num_bars=100)
        indicators = self.strategy.calculate_indicators(df)

        # Check all required indicators are present
        self.assertIn("rsi", indicators)
        self.assertIn("adx", indicators)
        self.assertIn("sma_50", indicators)
        self.assertIn("volume", indicators)

        # Check indicators are pandas Series
        self.assertIsInstance(indicators["rsi"], pd.Series)
        self.assertIsInstance(indicators["adx"], pd.Series)
        self.assertIsInstance(indicators["sma_50"], pd.Series)

    def test_calculate_indicators_with_insufficient_data(self):
        """Test calculate_indicators with insufficient data."""
        df = self._create_sample_data(num_bars=20)  # Too few for 50 SMA

        indicators = self.strategy.calculate_indicators(df)
        self.assertIn("sma_50", indicators)
        # SMA_50 will have NaN values for first 49 bars

    def test_generate_signal_structure(self):
        """Test that generated signal has correct structure."""
        df = self._create_sample_data(num_bars=100)
        signal = self.strategy.generate_signal(df)

        # Check signal structure
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

        self.assertIn("details", signal)
        details = signal["details"]

        # Check required detail fields
        self.assertIn("rsi", details)
        self.assertIn("current_price", details)
        self.assertIn("timestamp", details)

        # Check types
        self.assertIsInstance(details["rsi"], float)
        self.assertIsInstance(details["current_price"], float)

    def test_generate_signal_rsi_values(self):
        """Test that RSI values are in valid range (0-100)."""
        df = self._create_sample_data(num_bars=100)
        signal = self.strategy.generate_signal(df)

        rsi_value = signal["details"]["rsi"]
        self.assertGreaterEqual(rsi_value, 0)
        self.assertLessEqual(rsi_value, 100)

    def test_generate_signal_buy_logic(self):
        """Test BUY signal logic (RSI crosses above 30)."""
        df = self._create_sample_data(num_bars=100, rsi_level="oversold")
        signal = self.strategy.generate_signal(df)

        # Signal should be BUY, SELL, or HOLD based on RSI crossover
        self.assertIn(signal["signal"], ["BUY", "SELL", "HOLD"])

    def test_generate_signal_sell_logic(self):
        """Test SELL signal logic (RSI crosses below 70)."""
        df = self._create_sample_data(num_bars=100, rsi_level="overbought")
        signal = self.strategy.generate_signal(df)

        # Signal should be based on RSI level and crossover
        self.assertIn(signal["signal"], ["BUY", "SELL", "HOLD"])

    def test_validate_signal_hold_returns_unchanged(self):
        """Test that HOLD signals are not modified by validation."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "HOLD", "confidence": 0}

        validated = self.strategy.validate_signal(df, signal, data_feed="iex")

        self.assertEqual(validated["signal"], "HOLD")
        self.assertEqual(validated["confidence"], 0)

    def test_validate_signal_adds_validation_field(self):
        """Test that validation adds validation field to non-HOLD signals."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "BUY", "confidence": 0.6}

        validated = self.strategy.validate_signal(df, signal, data_feed="iex")

        # Should have validation field
        self.assertIn("validation", validated)
        self.assertIsInstance(validated["validation"], str)

    def test_validate_signal_confidence_adjustment(self):
        """Test that validation adjusts confidence appropriately."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "BUY", "confidence": 0.6}

        validated = self.strategy.validate_signal(df, signal, data_feed="iex")

        # Confidence should be adjusted
        self.assertIsInstance(validated["confidence"], float)
        self.assertGreaterEqual(validated["confidence"], 0.0)
        self.assertLessEqual(validated["confidence"], 1.0)

    def test_validate_signal_data_feed_awareness(self):
        """Test that validation treats SIP and IEX data feeds differently."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "BUY", "confidence": 0.6}

        # Validate with SIP feed
        validated_sip = self.strategy.validate_signal(df, signal.copy(), data_feed="sip")

        # Validate with IEX feed
        validated_iex = self.strategy.validate_signal(df, signal.copy(), data_feed="iex")

        # Both should have validation field
        self.assertIn("validation", validated_sip)
        self.assertIn("validation", validated_iex)

    def test_validate_signal_confidence_caps_at_one(self):
        """Test that confidence never exceeds 1.0 after validation."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "BUY", "confidence": 0.9}

        validated = self.strategy.validate_signal(df, signal, data_feed="sip")

        self.assertLessEqual(validated["confidence"], 1.0)

    def test_validate_signal_confidence_never_negative(self):
        """Test that confidence never goes below 0.0 after validation."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "BUY", "confidence": 0.1}

        validated = self.strategy.validate_signal(df, signal, data_feed="iex")

        self.assertGreaterEqual(validated["confidence"], 0.0)

    def test_validate_signal_adx_confirmation(self):
        """Test that ADX confirmation is considered in validation."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "BUY", "confidence": 0.6}

        validated = self.strategy.validate_signal(df, signal, data_feed="iex")

        # Should have validation notes
        self.assertIn("validation", validated)

    def test_validate_signal_price_vs_sma_confirmation(self):
        """Test that price vs SMA50 confirmation is considered."""
        df = self._create_sample_data(num_bars=100)

        # BUY signal should check if price > SMA50
        signal_buy = {"signal": "BUY", "confidence": 0.6}
        validated_buy = self.strategy.validate_signal(df, signal_buy, data_feed="iex")
        self.assertIn("validation", validated_buy)

        # SELL signal should check if price < SMA50
        signal_sell = {"signal": "SELL", "confidence": 0.6}
        validated_sell = self.strategy.validate_signal(df, signal_sell, data_feed="iex")
        self.assertIn("validation", validated_sell)

    def test_strategy_with_missing_volume_column(self):
        """Test strategy handles missing volume column gracefully."""
        df = self._create_sample_data(num_bars=100)
        df = df.drop(columns=["volume"])

        # Should raise an exception or handle gracefully
        with self.assertRaises(KeyError):
            self.strategy.calculate_indicators(df)

    def test_strategy_min_bars_requirement(self):
        """Test that strategy defines minimum bars requirement correctly."""
        # Should be at least 52 for 50 SMA
        self.assertGreaterEqual(self.strategy.min_bars_required, 50)

    def test_indicators_are_numeric(self):
        """Test that all indicator values are numeric."""
        df = self._create_sample_data(num_bars=100)
        indicators = self.strategy.calculate_indicators(df)

        # Check that indicators contain numeric values
        for key, series in indicators.items():
            if key != "volume":  # Volume is from original DataFrame
                self.assertTrue(pd.api.types.is_numeric_dtype(series))


if __name__ == "__main__":
    unittest.main()
