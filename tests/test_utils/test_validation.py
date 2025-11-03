"""
Tests for Input Validation Framework

Validates all validation utilities and custom exceptions.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.utils.validation import (
    validate_dataframe,
    validate_signal,
    validate_order,
    validate_config,
    validate_price_data,
    TradingError,
    DataValidationError,
    SignalValidationError,
    OrderValidationError,
    RateLimitError,
    ConfigurationError,
)


class TestDataframeValidation(unittest.TestCase):
    """Tests for dataframe validation."""

    def setUp(self):
        """Create valid test dataframe."""
        self.valid_df = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [101.0, 102.0, 103.0],
                "low": [99.0, 100.0, 101.0],
                "close": [100.5, 101.5, 102.5],
                "volume": [1000, 1100, 1200],
            }
        )

    def test_valid_dataframe_passes(self):
        """Test that valid dataframe passes validation."""
        result = validate_dataframe(self.valid_df)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)

    def test_empty_dataframe_fails(self):
        """Test that empty dataframe raises error."""
        with self.assertRaises(DataValidationError) as cm:
            validate_dataframe(pd.DataFrame(), min_rows=1)
        self.assertIn("0 rows", str(cm.exception))

    def test_missing_columns_fails(self):
        """Test that missing required columns raises error."""
        df_incomplete = pd.DataFrame({"open": [100], "close": [101]})
        with self.assertRaises(DataValidationError) as cm:
            validate_dataframe(df_incomplete)
        self.assertIn("missing required columns", str(cm.exception))
        self.assertIn("high", str(cm.exception))

    def test_nan_values_fail_by_default(self):
        """Test that NaN values raise error by default."""
        df_nan = self.valid_df.copy()
        df_nan.loc[1, "close"] = np.nan
        with self.assertRaises(DataValidationError) as cm:
            validate_dataframe(df_nan)
        self.assertIn("NaN values", str(cm.exception))

    def test_nan_values_allowed_when_specified(self):
        """Test that NaN values pass when allow_nan=True."""
        df_nan = self.valid_df.copy()
        df_nan.loc[1, "close"] = np.nan
        result = validate_dataframe(df_nan, allow_nan=True)
        self.assertIsNotNone(result)

    def test_high_less_than_low_fails(self):
        """Test that high < low raises error."""
        df_invalid = self.valid_df.copy()
        df_invalid.loc[0, "high"] = 98.0  # Less than low (99.0)
        with self.assertRaises(DataValidationError) as cm:
            validate_dataframe(df_invalid)
        self.assertIn("high < low", str(cm.exception))

    def test_high_less_than_close_fails(self):
        """Test that high < close raises error."""
        df_invalid = self.valid_df.copy()
        df_invalid.loc[0, "high"] = 99.0  # Less than close (100.5)
        with self.assertRaises(DataValidationError) as cm:
            validate_dataframe(df_invalid)
        self.assertIn("high less than", str(cm.exception))

    def test_low_greater_than_close_fails(self):
        """Test that low > close raises error."""
        df_invalid = self.valid_df.copy()
        df_invalid.loc[0, "low"] = 101.0  # Greater than close (100.5)
        with self.assertRaises(DataValidationError) as cm:
            validate_dataframe(df_invalid)
        self.assertIn("low greater than", str(cm.exception))

    def test_negative_prices_fail(self):
        """Test that negative prices raise error."""
        df_invalid = self.valid_df.copy()
        df_invalid.loc[0, "close"] = -10.0
        with self.assertRaises(DataValidationError) as cm:
            validate_dataframe(df_invalid)
        self.assertIn("non-positive prices", str(cm.exception))

    def test_negative_volume_fails(self):
        """Test that negative volume raises error."""
        df_invalid = self.valid_df.copy()
        df_invalid.loc[0, "volume"] = -1000
        with self.assertRaises(DataValidationError) as cm:
            validate_dataframe(df_invalid)
        self.assertIn("negative volume", str(cm.exception))

    def test_unsorted_index_fails(self):
        """Test that unsorted datetime index raises error."""
        df_unsorted = self.valid_df.copy()
        dates = [datetime(2025, 1, 3), datetime(2025, 1, 1), datetime(2025, 1, 2)]
        df_unsorted.index = pd.DatetimeIndex(dates)
        with self.assertRaises(DataValidationError) as cm:
            validate_dataframe(df_unsorted)
        self.assertIn("not sorted", str(cm.exception))


class TestSignalValidation(unittest.TestCase):
    """Tests for signal validation."""

    def setUp(self):
        """Create valid test signal."""
        self.valid_signal = {
            "action": "BUY",
            "confidence": 0.75,
            "reasoning": "Strong uptrend with volume confirmation",
            "entry_price": 100.0,
            "stop_loss": 95.0,
            "take_profit": 110.0,
            "position_size": 100,
        }

    def test_valid_signal_passes(self):
        """Test that valid signal passes validation."""
        result = validate_signal(self.valid_signal)
        self.assertEqual(result["action"], "BUY")
        self.assertEqual(result["confidence"], 0.75)

    def test_missing_action_fails(self):
        """Test that missing action raises error."""
        signal = self.valid_signal.copy()
        del signal["action"]
        with self.assertRaises(SignalValidationError) as cm:
            validate_signal(signal)
        self.assertIn("missing required fields", str(cm.exception))

    def test_invalid_action_fails(self):
        """Test that invalid action raises error."""
        signal = self.valid_signal.copy()
        signal["action"] = "HODL"
        with self.assertRaises(SignalValidationError) as cm:
            validate_signal(signal)
        self.assertIn("not in", str(cm.exception))

    def test_confidence_out_of_range_fails(self):
        """Test that confidence outside [0, 1] raises error."""
        signal = self.valid_signal.copy()
        signal["confidence"] = 1.5
        with self.assertRaises(SignalValidationError) as cm:
            validate_signal(signal)
        self.assertIn("between 0 and 1", str(cm.exception))

    def test_negative_confidence_fails(self):
        """Test that negative confidence raises error."""
        signal = self.valid_signal.copy()
        signal["confidence"] = -0.5
        with self.assertRaises(SignalValidationError) as cm:
            validate_signal(signal)
        self.assertIn("between 0 and 1", str(cm.exception))

    def test_buy_signal_stop_greater_than_entry_fails(self):
        """Test that BUY signal with stop > entry raises error."""
        signal = self.valid_signal.copy()
        signal["stop_loss"] = 105.0  # Greater than entry (100.0)
        with self.assertRaises(SignalValidationError) as cm:
            validate_signal(signal)
        self.assertIn("must be <", str(cm.exception))

    def test_buy_signal_target_less_than_entry_fails(self):
        """Test that BUY signal with target < entry raises error."""
        signal = self.valid_signal.copy()
        signal["take_profit"] = 95.0  # Less than entry (100.0)
        with self.assertRaises(SignalValidationError) as cm:
            validate_signal(signal)
        self.assertIn("must be >", str(cm.exception))

    def test_sell_signal_validation(self):
        """Test that SELL signal validates correctly."""
        signal = {
            "action": "SELL",
            "confidence": 0.8,
            "entry_price": 100.0,
            "stop_loss": 105.0,  # Stop above entry for SELL
            "take_profit": 90.0,  # Target below entry for SELL
        }
        result = validate_signal(signal)
        self.assertEqual(result["action"], "SELL")

    def test_sell_signal_invalid_stop_fails(self):
        """Test that SELL signal with stop <= entry raises error."""
        signal = {
            "action": "SELL",
            "confidence": 0.8,
            "entry_price": 100.0,
            "stop_loss": 95.0,  # Should be > entry for SELL
            "take_profit": 90.0,
        }
        with self.assertRaises(SignalValidationError) as cm:
            validate_signal(signal)
        self.assertIn("must be >", str(cm.exception))

    def test_hold_signal_passes(self):
        """Test that HOLD signal passes with minimal fields."""
        signal = {"action": "HOLD", "confidence": 0.5}
        result = validate_signal(signal)
        self.assertEqual(result["action"], "HOLD")


class TestOrderValidation(unittest.TestCase):
    """Tests for order validation."""

    def test_valid_market_order_passes(self):
        """Test that valid market order passes validation."""
        result = validate_order("AAPL", 100, "BUY", "market")
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["quantity"], 100)
        self.assertEqual(result["side"], "BUY")

    def test_empty_symbol_fails(self):
        """Test that empty symbol raises error."""
        with self.assertRaises(OrderValidationError) as cm:
            validate_order("", 100, "BUY")
        self.assertIn("non-empty string", str(cm.exception))

    def test_negative_quantity_fails(self):
        """Test that negative quantity raises error."""
        with self.assertRaises(OrderValidationError) as cm:
            validate_order("AAPL", -100, "BUY")
        self.assertIn("must be positive", str(cm.exception))

    def test_excessive_quantity_fails(self):
        """Test that excessive quantity raises error."""
        with self.assertRaises(OrderValidationError) as cm:
            validate_order("AAPL", 2_000_000, "BUY")
        self.assertIn("safety limit", str(cm.exception))

    def test_invalid_side_fails(self):
        """Test that invalid side raises error."""
        with self.assertRaises(OrderValidationError) as cm:
            validate_order("AAPL", 100, "HOLD")
        self.assertIn("not in", str(cm.exception))

    def test_limit_order_without_price_fails(self):
        """Test that limit order without limit_price raises error."""
        with self.assertRaises(OrderValidationError) as cm:
            validate_order("AAPL", 100, "BUY", "limit")
        self.assertIn("requires limit_price", str(cm.exception))

    def test_limit_order_with_price_passes(self):
        """Test that limit order with limit_price passes."""
        result = validate_order("AAPL", 100, "BUY", "limit", limit_price=150.0)
        self.assertEqual(result["limit_price"], 150.0)

    def test_stop_order_without_price_fails(self):
        """Test that stop order without stop_price raises error."""
        with self.assertRaises(OrderValidationError) as cm:
            validate_order("AAPL", 100, "BUY", "stop")
        self.assertIn("requires stop_price", str(cm.exception))

    def test_stop_limit_order_passes(self):
        """Test that stop_limit order with both prices passes."""
        result = validate_order("AAPL", 100, "BUY", "stop_limit", limit_price=150.0, stop_price=145.0)
        self.assertEqual(result["limit_price"], 150.0)
        self.assertEqual(result["stop_price"], 145.0)


class TestConfigValidation(unittest.TestCase):
    """Tests for configuration validation."""

    def test_valid_config_passes(self):
        """Test that valid config passes validation."""
        config = {"api_key": "test123", "secret": "secret456", "base_url": "https://api.test"}
        result = validate_config(config, ["api_key", "secret", "base_url"])
        self.assertEqual(result["api_key"], "test123")

    def test_missing_keys_fails(self):
        """Test that missing required keys raises error."""
        config = {"api_key": "test123"}
        with self.assertRaises(ConfigurationError) as cm:
            validate_config(config, ["api_key", "secret", "base_url"])
        self.assertIn("missing required keys", str(cm.exception))

    def test_none_values_fail(self):
        """Test that None values for required keys raise error."""
        config = {"api_key": "test123", "secret": None, "base_url": "https://api.test"}
        with self.assertRaises(ConfigurationError) as cm:
            validate_config(config, ["api_key", "secret", "base_url"])
        self.assertIn("None values", str(cm.exception))


class TestExceptionHierarchy(unittest.TestCase):
    """Tests for custom exception hierarchy."""

    def test_exception_inheritance(self):
        """Test that all exceptions inherit from TradingError."""
        self.assertTrue(issubclass(DataValidationError, TradingError))
        self.assertTrue(issubclass(SignalValidationError, TradingError))
        self.assertTrue(issubclass(OrderValidationError, TradingError))
        self.assertTrue(issubclass(RateLimitError, TradingError))
        self.assertTrue(issubclass(ConfigurationError, TradingError))

    def test_exception_catching(self):
        """Test that TradingError catches all specific errors."""
        try:
            raise DataValidationError("Test error")
        except TradingError:
            pass  # Should catch

        try:
            raise SignalValidationError("Test error")
        except TradingError:
            pass  # Should catch


if __name__ == "__main__":
    unittest.main(verbosity=2)
