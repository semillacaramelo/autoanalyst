"""
Input Validation Framework

Comprehensive validation utilities for trading system inputs.
Catches invalid data before it causes errors in downstream processing.

Features:
- OHLCV dataframe validation (required columns, types, ranges)
- Signal schema validation (action, confidence, price levels)
- Order validation (symbol, quantity, price constraints)
- Custom exception hierarchy for different error types
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TradingError(Exception):
    """Base exception for all trading-related errors."""

    pass


class DataValidationError(TradingError):
    """Raised when input data fails validation checks."""

    pass


class SignalValidationError(TradingError):
    """Raised when trading signal has invalid format or values."""

    pass


class OrderValidationError(TradingError):
    """Raised when order parameters are invalid."""

    pass


class RateLimitError(TradingError):
    """Raised when API rate limits are exceeded."""

    pass


class ConfigurationError(TradingError):
    """Raised when configuration is invalid or missing."""

    pass


def validate_dataframe(
    df: pd.DataFrame,
    required_columns: Optional[List[str]] = None,
    min_rows: int = 1,
    allow_nan: bool = False,
    check_sorted: bool = True,
    name: str = "dataframe",
) -> pd.DataFrame:
    """
    Validate OHLCV dataframe meets all requirements.

    Args:
        df: DataFrame to validate
        required_columns: List of required column names (default: OHLCV)
        min_rows: Minimum number of rows required
        allow_nan: Whether NaN values are acceptable
        check_sorted: Verify index is sorted (for time series)
        name: Name for error messages

    Returns:
        Validated dataframe (unchanged if valid)

    Raises:
        DataValidationError: If validation fails

    Examples:
        >>> df = pd.DataFrame({'open': [100], 'high': [101], 'low': [99], 'close': [100.5], 'volume': [1000]})
        >>> validated = validate_dataframe(df)  # Returns df if valid
        >>> validate_dataframe(pd.DataFrame())  # Raises DataValidationError
    """
    if not isinstance(df, pd.DataFrame):
        raise DataValidationError(f"{name} must be a pandas DataFrame, got {type(df)}")

    # Check minimum rows
    if len(df) < min_rows:
        raise DataValidationError(f"{name} has {len(df)} rows, minimum required is {min_rows}")

    # Check required columns
    if required_columns is None:
        required_columns = ["open", "high", "low", "close", "volume"]

    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        raise DataValidationError(
            f"{name} missing required columns: {missing_cols}. " f"Available columns: {list(df.columns)}"
        )

    # Check for NaN values
    if not allow_nan:
        nan_cols = df[required_columns].columns[df[required_columns].isna().any()].tolist()
        if nan_cols:
            nan_counts = {col: df[col].isna().sum() for col in nan_cols}
            raise DataValidationError(f"{name} contains NaN values in columns: {nan_counts}")

    # Check OHLCV constraints (if applicable)
    if all(col in df.columns for col in ["open", "high", "low", "close"]):
        # Prices should be positive (check first before relationships)
        price_cols = ["open", "high", "low", "close"]
        if (df[price_cols] <= 0).any().any():
            raise DataValidationError(f"{name} has non-positive prices")

        # High should be >= low
        if (df["high"] < df["low"]).any():
            invalid_rows = df[df["high"] < df["low"]].index.tolist()
            raise DataValidationError(f"{name} has high < low in rows: {invalid_rows[:5]}")

        # High should be >= open and close
        if (df["high"] < df["open"]).any() or (df["high"] < df["close"]).any():
            raise DataValidationError(f"{name} has high less than open or close")

        # Low should be <= open and close
        if (df["low"] > df["open"]).any() or (df["low"] > df["close"]).any():
            raise DataValidationError(f"{name} has low greater than open or close")

    # Check volume is non-negative
    if "volume" in df.columns:
        if (df["volume"] < 0).any():
            raise DataValidationError(f"{name} has negative volume values")

    # Check index is sorted (for time series)
    if check_sorted and isinstance(df.index, pd.DatetimeIndex):
        if not df.index.is_monotonic_increasing:
            raise DataValidationError(f"{name} index is not sorted chronologically")

    return df


def validate_signal(signal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate trading signal has correct structure and values.

    Args:
        signal: Signal dictionary from strategy

    Returns:
        Validated signal (unchanged if valid)

    Raises:
        SignalValidationError: If signal is invalid

    Expected structure:
        {
            'action': 'BUY' | 'SELL' | 'HOLD',
            'confidence': float (0.0 to 1.0),
            'reasoning': str,
            'entry_price': float (optional),
            'stop_loss': float (optional),
            'take_profit': float (optional),
            'position_size': float (optional),
        }
    """
    if not isinstance(signal, dict):
        raise SignalValidationError(f"Signal must be a dictionary, got {type(signal)}")

    # Check required fields
    required_fields = ["action", "confidence"]
    missing_fields = set(required_fields) - set(signal.keys())
    if missing_fields:
        raise SignalValidationError(
            f"Signal missing required fields: {missing_fields}. " f"Available fields: {list(signal.keys())}"
        )

    # Validate action
    valid_actions = ["BUY", "SELL", "HOLD"]
    if signal["action"] not in valid_actions:
        raise SignalValidationError(f"Signal action '{signal['action']}' not in {valid_actions}")

    # Validate confidence
    confidence = signal["confidence"]
    if not isinstance(confidence, (int, float)):
        raise SignalValidationError(f"Confidence must be numeric, got {type(confidence)}")
    if not 0.0 <= confidence <= 1.0:
        raise SignalValidationError(f"Confidence must be between 0 and 1, got {confidence}")

    # Validate optional price levels
    price_fields = ["entry_price", "stop_loss", "take_profit"]
    for field in price_fields:
        if field in signal:
            price = signal[field]
            if price is not None:
                if not isinstance(price, (int, float)):
                    raise SignalValidationError(f"{field} must be numeric, got {type(price)}")
                if price <= 0:
                    raise SignalValidationError(f"{field} must be positive, got {price}")

    # Validate stop loss < entry < take profit (for BUY)
    if signal["action"] == "BUY" and all(field in signal for field in ["entry_price", "stop_loss", "take_profit"]):
        entry = signal["entry_price"]
        stop = signal["stop_loss"]
        target = signal["take_profit"]

        if stop is not None and entry is not None and stop >= entry:
            raise SignalValidationError(f"BUY signal: stop_loss ({stop}) must be < entry_price ({entry})")
        if target is not None and entry is not None and target <= entry:
            raise SignalValidationError(f"BUY signal: take_profit ({target}) must be > entry_price ({entry})")

    # Validate stop loss > entry > take profit (for SELL)
    if signal["action"] == "SELL" and all(field in signal for field in ["entry_price", "stop_loss", "take_profit"]):
        entry = signal["entry_price"]
        stop = signal["stop_loss"]
        target = signal["take_profit"]

        if stop is not None and entry is not None and stop <= entry:
            raise SignalValidationError(f"SELL signal: stop_loss ({stop}) must be > entry_price ({entry})")
        if target is not None and entry is not None and target >= entry:
            raise SignalValidationError(f"SELL signal: take_profit ({target}) must be < entry_price ({entry})")

    # Validate position size
    if "position_size" in signal and signal["position_size"] is not None:
        size = signal["position_size"]
        if not isinstance(size, (int, float)):
            raise SignalValidationError(f"position_size must be numeric, got {type(size)}")
        if size <= 0:
            raise SignalValidationError(f"position_size must be positive, got {size}")

    return signal


def validate_order(
    symbol: str,
    quantity: Union[int, float],
    side: str,
    order_type: str = "market",
    limit_price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Validate order parameters before submission.

    Args:
        symbol: Trading symbol (e.g., 'AAPL', 'BTC/USD')
        quantity: Number of shares/units to trade
        side: 'BUY' or 'SELL'
        order_type: 'market', 'limit', 'stop', 'stop_limit'
        limit_price: Limit price for limit orders
        stop_price: Stop price for stop orders

    Returns:
        Dictionary with validated order parameters

    Raises:
        OrderValidationError: If any parameter is invalid
    """
    # Validate symbol
    if not isinstance(symbol, str) or not symbol.strip():
        raise OrderValidationError(f"Symbol must be non-empty string, got {symbol}")

    symbol = symbol.strip().upper()

    # Validate quantity
    if not isinstance(quantity, (int, float)):
        raise OrderValidationError(f"Quantity must be numeric, got {type(quantity)}")
    if quantity <= 0:
        raise OrderValidationError(f"Quantity must be positive, got {quantity}")
    if quantity > 1_000_000:
        raise OrderValidationError(f"Quantity {quantity} exceeds safety limit (1,000,000)")

    # Validate side
    valid_sides = ["BUY", "SELL"]
    side = side.upper()
    if side not in valid_sides:
        raise OrderValidationError(f"Side '{side}' not in {valid_sides}")

    # Validate order type
    valid_types = ["market", "limit", "stop", "stop_limit"]
    order_type = order_type.lower()
    if order_type not in valid_types:
        raise OrderValidationError(f"Order type '{order_type}' not in {valid_types}")

    # Validate limit price for limit orders
    if order_type in ["limit", "stop_limit"]:
        if limit_price is None:
            raise OrderValidationError(f"{order_type} order requires limit_price")
        if not isinstance(limit_price, (int, float)):
            raise OrderValidationError(f"limit_price must be numeric, got {type(limit_price)}")
        if limit_price <= 0:
            raise OrderValidationError(f"limit_price must be positive, got {limit_price}")

    # Validate stop price for stop orders
    if order_type in ["stop", "stop_limit"]:
        if stop_price is None:
            raise OrderValidationError(f"{order_type} order requires stop_price")
        if not isinstance(stop_price, (int, float)):
            raise OrderValidationError(f"stop_price must be numeric, got {type(stop_price)}")
        if stop_price <= 0:
            raise OrderValidationError(f"stop_price must be positive, got {stop_price}")

    return {
        "symbol": symbol,
        "quantity": quantity,
        "side": side,
        "order_type": order_type,
        "limit_price": limit_price,
        "stop_price": stop_price,
        "validated_at": datetime.now().isoformat(),
    }


def validate_config(config: Dict[str, Any], required_keys: List[str]) -> Dict[str, Any]:
    """
    Validate configuration dictionary has all required keys.

    Args:
        config: Configuration dictionary
        required_keys: List of required key names

    Returns:
        Validated config (unchanged if valid)

    Raises:
        ConfigurationError: If required keys are missing or values are invalid
    """
    if not isinstance(config, dict):
        raise ConfigurationError(f"Config must be a dictionary, got {type(config)}")

    missing_keys = set(required_keys) - set(config.keys())
    if missing_keys:
        raise ConfigurationError(
            f"Configuration missing required keys: {missing_keys}. " f"Available keys: {list(config.keys())}"
        )

    # Check for None values in required keys
    none_keys = [k for k in required_keys if config.get(k) is None]
    if none_keys:
        raise ConfigurationError(f"Configuration has None values for required keys: {none_keys}")

    return config


# Convenience function for common validation patterns
def validate_price_data(df: pd.DataFrame, name: str = "price data") -> pd.DataFrame:
    """
    Validate price data with standard OHLCV requirements.

    This is a convenience wrapper around validate_dataframe with sensible defaults.
    """
    return validate_dataframe(
        df=df,
        required_columns=["open", "high", "low", "close", "volume"],
        min_rows=1,
        allow_nan=False,
        check_sorted=True,
        name=name,
    )
