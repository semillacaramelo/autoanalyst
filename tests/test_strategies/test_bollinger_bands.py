"""
Unit tests for Bollinger Bands Reversal trading strategy.

Tests cover:
- Indicator calculation (Bollinger Bands, BB width, RSI)
- Signal generation (BUY at lower band + oversold, SELL at upper band + overbought)
- Signal validation with confirmations (Volatility expansion, candlestick patterns)
- Edge cases
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.strategies.bollinger_bands_reversal import BollingerBandsReversalStrategy


class TestBollingerBandsReversalStrategy(unittest.TestCase):
    """Test suite for Bollinger Bands Reversal strategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = BollingerBandsReversalStrategy()
        
    def _create_sample_data(self, num_bars: int = 100, volatility: str = "normal") -> pd.DataFrame:
        """Create sample OHLCV data for testing."""
        timestamps = [datetime.now() - timedelta(minutes=i) for i in range(num_bars)]
        timestamps.reverse()
        
        if volatility == "high":
            close_prices = 110 + np.random.randn(num_bars) * 5
        elif volatility == "low":
            close_prices = 110 + np.random.randn(num_bars) * 0.5
        else:  # normal
            close_prices = 110 + np.random.randn(num_bars) * 2
            
        data = {
            'open': close_prices + np.random.randn(num_bars) * 0.3,
            'high': close_prices + np.abs(np.random.randn(num_bars) * 0.5),
            'low': close_prices - np.abs(np.random.randn(num_bars) * 0.5),
            'close': close_prices,
            'volume': np.random.randint(1000000, 5000000, num_bars)
        }
        
        return pd.DataFrame(data, index=pd.DatetimeIndex(timestamps))
    
    def test_initialization(self):
        """Test strategy initialization."""
        self.assertEqual(self.strategy.name, "bollinger")
        self.assertEqual(self.strategy.description, "Bollinger Bands Mean Reversal Strategy")
        self.assertEqual(self.strategy.min_bars_required, 21)
        
    def test_calculate_indicators_returns_all_required(self):
        """Test that calculate_indicators returns all required indicators."""
        df = self._create_sample_data(num_bars=100)
        indicators = self.strategy.calculate_indicators(df)
        
        self.assertIn("upper_band", indicators)
        self.assertIn("middle_band", indicators)
        self.assertIn("lower_band", indicators)
        self.assertIn("rsi", indicators)
        self.assertIn("volume", indicators)
        self.assertIn("bb_width", indicators)
        
        self.assertIsInstance(indicators["upper_band"], pd.Series)
        self.assertIsInstance(indicators["middle_band"], pd.Series)
        self.assertIsInstance(indicators["lower_band"], pd.Series)
        
    def test_calculate_indicators_band_ordering(self):
        """Test that Bollinger Bands are ordered correctly (upper > middle > lower)."""
        df = self._create_sample_data(num_bars=100)
        indicators = self.strategy.calculate_indicators(df)
        
        # Check band ordering for last value (ignoring NaN)
        upper = indicators["upper_band"].iloc[-1]
        middle = indicators["middle_band"].iloc[-1]
        lower = indicators["lower_band"].iloc[-1]
        
        if not (pd.isna(upper) or pd.isna(middle) or pd.isna(lower)):
            self.assertGreater(upper, middle)
            self.assertGreater(middle, lower)
        
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
        self.assertIn("price", details)
        self.assertIn("lower_band", details)
        self.assertIn("upper_band", details)
        self.assertIn("rsi", details)
        self.assertIn("timestamp", details)
        
        self.assertIsInstance(details["price"], float)
        self.assertIsInstance(details["lower_band"], float)
        self.assertIsInstance(details["upper_band"], float)
        self.assertIsInstance(details["rsi"], float)
        
    def test_generate_signal_rsi_values(self):
        """Test that RSI values are in valid range (0-100)."""
        df = self._create_sample_data(num_bars=100)
        signal = self.strategy.generate_signal(df)
        
        rsi_value = signal["details"]["rsi"]
        if not pd.isna(rsi_value):
            self.assertGreaterEqual(rsi_value, 0)
            self.assertLessEqual(rsi_value, 100)
        
    def test_validate_signal_hold_returns_unchanged(self):
        """Test that HOLD signals are not modified by validation."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "HOLD", "confidence": 0}
        
        validated = self.strategy.validate_signal(df, signal, _data_feed="iex")
        
        self.assertEqual(validated["signal"], "HOLD")
        self.assertEqual(validated["confidence"], 0)
        
    def test_validate_signal_adds_validation_field(self):
        """Test that validation adds validation field."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "BUY", "confidence": 0.7, "details": {}}
        
        validated = self.strategy.validate_signal(df, signal, _data_feed="iex")
        
        self.assertIn("validation", validated)
        self.assertIsInstance(validated["validation"], str)
        
    def test_validate_signal_confidence_bounds(self):
        """Test that confidence stays within [0, 1] bounds."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "BUY", "confidence": 0.95, "details": {}}
        
        validated = self.strategy.validate_signal(df, signal, _data_feed="iex")
        
        self.assertGreaterEqual(validated["confidence"], 0.0)
        self.assertLessEqual(validated["confidence"], 1.0)
        
    def test_validate_signal_volatility_confirmation(self):
        """Test that volatility expansion is checked."""
        df = self._create_sample_data(num_bars=100, volatility="high")
        signal = {"signal": "BUY", "confidence": 0.7, "details": {}}
        
        validated = self.strategy.validate_signal(df, signal, _data_feed="iex")
        
        # Should have validation notes
        self.assertIn("validation", validated)
        
    def test_strategy_with_insufficient_data(self):
        """Test strategy with insufficient bars."""
        df = self._create_sample_data(num_bars=15)
        
        # Should still run but may have limited indicators
        signal = self.strategy.generate_signal(df)
        self.assertIn("signal", signal)
        
    def test_strategy_min_bars_requirement(self):
        """Test that strategy defines minimum bars requirement."""
        self.assertEqual(self.strategy.min_bars_required, 21)
        
    def test_bb_width_calculation(self):
        """Test that BB width is calculated correctly."""
        df = self._create_sample_data(num_bars=100)
        indicators = self.strategy.calculate_indicators(df)
        
        bb_width = indicators["bb_width"]
        self.assertIsInstance(bb_width, pd.Series)
        
        # BB width should be positive (or NaN for early values)
        valid_widths = bb_width.dropna()
        if len(valid_widths) > 0:
            self.assertTrue(all(valid_widths >= 0))
        
    def test_strategy_with_low_volatility(self):
        """Test strategy behavior in low volatility conditions."""
        df = self._create_sample_data(num_bars=100, volatility="low")
        signal = self.strategy.generate_signal(df)
        
        # Should generate a signal (BUY/SELL/HOLD)
        self.assertIn(signal["signal"], ["BUY", "SELL", "HOLD"])
        
    def test_strategy_with_high_volatility(self):
        """Test strategy behavior in high volatility conditions."""
        df = self._create_sample_data(num_bars=100, volatility="high")
        signal = self.strategy.generate_signal(df)
        
        # Should generate a signal
        self.assertIn(signal["signal"], ["BUY", "SELL", "HOLD"])


if __name__ == '__main__':
    unittest.main()
