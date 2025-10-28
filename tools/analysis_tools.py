import pandas as pd
from typing import Optional

def calculate_3ma_signal(
    historical_data: pd.DataFrame,
    short_window: int = 8,
    medium_window: int = 13,
    long_window: int = 21,
) -> Optional[str]:
    """
    Calculates a trading signal based on a triple moving average (3MA) strategy.

    Args:
        historical_data (pd.DataFrame): DataFrame with a 'close' column.
        short_window (int): The window for the short moving average.
        medium_window (int): The window for the medium moving average.
        long_window (int): The window for the long moving average.

    Returns:
        Optional[str]: 'BUY', 'SELL', 'HOLD', or None if data is insufficient.
    """
    if historical_data is None or len(historical_data) < long_window:
        print(f"Warning: Insufficient data for 3MA calculation. Need at least {long_window} data points.")
        return None

    # Calculate the three moving averages
    try:
        historical_data['ma_short'] = historical_data['close'].rolling(window=short_window).mean()
        historical_data['ma_medium'] = historical_data['close'].rolling(window=medium_window).mean()
        historical_data['ma_long'] = historical_data['close'].rolling(window=long_window).mean()

        # Get the most recent values for each moving average
        last_ma_short = historical_data['ma_short'].iloc[-1]
        last_ma_medium = historical_data['ma_medium'].iloc[-1]
        last_ma_long = historical_data['ma_long'].iloc[-1]

        # Determine the signal
        if last_ma_short > last_ma_medium > last_ma_long:
            return 'BUY'
        elif last_ma_short < last_ma_medium < last_ma_long:
            return 'SELL'
        else:
            return 'HOLD'

    except Exception as e:
        print(f"An error occurred during 3MA calculation: {e}")
        return None
