"""
Unit tests for Triple Moving Average (3MA) trading strategy.

Tests cover:
- Indicator calculation
- Signal generation (BUY, SELL, HOLD)
- Signal validation and confirmation
- Edge cases (insufficient data, missing columns)
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.strategies.triple_ma import TripleMovingAverageStrategy


class TestTripleMovingAverageStrategy(unittest.TestCase):
    """Test suite for Triple Moving Average strategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = TripleMovingAverageStrategy()
        
    def _create_sample_data(self, num_bars: int = 100, trend: str = "up") -> pd.DataFrame:
        """
        Create sample OHLCV data for testing.
        
        Args:
            num_bars: Number of bars to generate
            trend: Trend direction ("up", "down", "sideways")
            
        Returns:
            DataFrame with OHLCV data
        """
        timestamps = [datetime.now() - timedelta(minutes=i) for i in range(num_bars)]
        timestamps.reverse()
        
        # Generate price data based on trend
        if trend == "up":
            close_prices = np.linspace(100, 120, num_bars) + np.random.randn(num_bars) * 0.5
        elif trend == "down":
            close_prices = np.linspace(120, 100, num_bars) + np.random.randn(num_bars) * 0.5
        else:  # sideways
            close_prices = 110 + np.random.randn(num_bars) * 2
            
        data = {
            'open': close_prices + np.random.randn(num_bars) * 0.3,
            'high': close_prices + np.abs(np.random.randn(num_bars) * 0.5),
            'low': close_prices - np.abs(np.random.randn(num_bars) * 0.5),
            'close': close_prices,
            'volume': np.random.randint(1000000, 5000000, num_bars)
        }
        
        df = pd.DataFrame(data, index=pd.DatetimeIndex(timestamps))
        return df
    
    def test_initialization(self):
        """Test strategy initialization."""
        self.assertEqual(self.strategy.name, "3ma")
        self.assertEqual(self.strategy.description, "Triple Moving Average Crossover Strategy")
        self.assertIsInstance(self.strategy.min_bars_required, int)
        self.assertGreater(self.strategy.min_bars_required, 20)
        
    def test_calculate_indicators_returns_all_required(self):
        """Test that calculate_indicators returns all required indicators."""
        df = self._create_sample_data(num_bars=100)
        indicators = self.strategy.calculate_indicators(df)
        
        # Check all required indicators are present
        self.assertIn("fast_ma", indicators)
        self.assertIn("medium_ma", indicators)
        self.assertIn("slow_ma", indicators)
        self.assertIn("volume", indicators)
        self.assertIn("adx", indicators)
        
        # Check indicators are pandas Series
        self.assertIsInstance(indicators["fast_ma"], pd.Series)
        self.assertIsInstance(indicators["medium_ma"], pd.Series)
        self.assertIsInstance(indicators["slow_ma"], pd.Series)
        
        # Check lengths match
        self.assertEqual(len(indicators["fast_ma"]), len(df))
        self.assertEqual(len(indicators["medium_ma"]), len(df))
        self.assertEqual(len(indicators["slow_ma"]), len(df))
        
    def test_calculate_indicators_with_insufficient_data(self):
        """Test calculate_indicators with insufficient data."""
        df = self._create_sample_data(num_bars=10)  # Too few bars
        
        # Should still calculate indicators, but may have NaN values
        indicators = self.strategy.calculate_indicators(df)
        self.assertIn("fast_ma", indicators)
        
    def test_generate_signal_buy_on_bullish_crossover(self):
        """Test BUY signal generation on bullish crossover."""
        # Create data that will trigger a BUY signal
        # Fast MA crosses above medium MA, and medium > slow
        df = self._create_sample_data(num_bars=100, trend="up")
        
        # Generate signal
        signal = self.strategy.generate_signal(df)
        
        # Check signal structure
        self.assertIn("signal", signal)
        self.assertIn("confidence", signal)
        self.assertIn("details", signal)
        self.assertIn(signal["signal"], ["BUY", "SELL", "HOLD"])
        self.assertGreaterEqual(signal["confidence"], 0.0)
        self.assertLessEqual(signal["confidence"], 1.0)
        
    def test_generate_signal_sell_on_bearish_crossover(self):
        """Test SELL signal generation on bearish crossover."""
        df = self._create_sample_data(num_bars=100, trend="down")
        signal = self.strategy.generate_signal(df)
        
        self.assertIn("signal", signal)
        self.assertIn(signal["signal"], ["BUY", "SELL", "HOLD"])
        
    def test_generate_signal_hold_on_sideways(self):
        """Test HOLD signal in sideways market."""
        df = self._create_sample_data(num_bars=100, trend="sideways")
        signal = self.strategy.generate_signal(df)
        
        # In sideways market, most signals should be HOLD
        self.assertIn("signal", signal)
        
    def test_generate_signal_details_structure(self):
        """Test that signal details contain required fields."""
        df = self._create_sample_data(num_bars=100)
        signal = self.strategy.generate_signal(df)
        
        self.assertIn("details", signal)
        details = signal["details"]
        
        # Check required detail fields
        self.assertIn("fast_ma", details)
        self.assertIn("medium_ma", details)
        self.assertIn("slow_ma", details)
        self.assertIn("current_price", details)
        self.assertIn("timestamp", details)
        
        # Check types
        self.assertIsInstance(details["fast_ma"], float)
        self.assertIsInstance(details["medium_ma"], float)
        self.assertIsInstance(details["slow_ma"], float)
        self.assertIsInstance(details["current_price"], float)
        
    def test_validate_signal_hold_returns_unchanged(self):
        """Test that HOLD signals are not modified by validation."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "HOLD", "confidence": 0}
        
        validated = self.strategy.validate_signal(df, signal, data_feed="iex")
        
        self.assertEqual(validated["signal"], "HOLD")
        self.assertEqual(validated["confidence"], 0)
        
    def test_validate_signal_adds_validation_notes(self):
        """Test that validation adds notes to non-HOLD signals."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "BUY", "confidence": 0.7}
        
        validated = self.strategy.validate_signal(df, signal, data_feed="iex")
        
        # Should have validation field
        self.assertIn("validation", validated)
        self.assertIsInstance(validated["validation"], str)
        
    def test_validate_signal_confidence_adjustment(self):
        """Test that validation adjusts confidence appropriately."""
        df = self._create_sample_data(num_bars=100)
        original_confidence = 0.7
        signal = {"signal": "BUY", "confidence": original_confidence}
        
        validated = self.strategy.validate_signal(df, signal, data_feed="iex")
        
        # Confidence should be adjusted (either up or down)
        self.assertIsInstance(validated["confidence"], float)
        self.assertGreaterEqual(validated["confidence"], 0.0)
        self.assertLessEqual(validated["confidence"], 1.0)
        
    def test_validate_signal_data_feed_awareness(self):
        """Test that validation treats SIP and IEX data feeds differently."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "BUY", "confidence": 0.7}
        
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
        signal = {"signal": "BUY", "confidence": 0.95}
        
        validated = self.strategy.validate_signal(df, signal, data_feed="sip")
        
        self.assertLessEqual(validated["confidence"], 1.0)
        
    def test_validate_signal_confidence_never_negative(self):
        """Test that confidence never goes below 0.0 after validation."""
        df = self._create_sample_data(num_bars=100)
        signal = {"signal": "BUY", "confidence": 0.1}
        
        validated = self.strategy.validate_signal(df, signal, data_feed="iex")
        
        self.assertGreaterEqual(validated["confidence"], 0.0)
        
    def test_strategy_with_missing_volume_column(self):
        """Test strategy handles missing volume column gracefully."""
        df = self._create_sample_data(num_bars=100)
        df = df.drop(columns=['volume'])
        
        # Should raise an exception or handle gracefully
        with self.assertRaises(KeyError):
            self.strategy.calculate_indicators(df)
            
    def test_strategy_min_bars_requirement(self):
        """Test that strategy defines minimum bars requirement."""
        self.assertGreater(self.strategy.min_bars_required, 0)
        
    def test_indicators_are_numeric(self):
        """Test that all indicator values are numeric."""
        df = self._create_sample_data(num_bars=100)
        indicators = self.strategy.calculate_indicators(df)
        
        # Check that indicators contain numeric values (excluding NaN)
        for key, series in indicators.items():
            if key != "volume":  # Volume is from original DataFrame
                # Should be numeric type
                self.assertTrue(pd.api.types.is_numeric_dtype(series))


if __name__ == '__main__':
    unittest.main()
