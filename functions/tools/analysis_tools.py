import pandas as pd
from typing import Optional, List, Dict, Any
from tools.alpaca_tools import get_trade_history

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

    try:
        historical_data['ma_short'] = historical_data['close'].rolling(window=short_window).mean()
        historical_data['ma_medium'] = historical_data['close'].rolling(window=medium_window).mean()
        historical_data['ma_long'] = historical_data['close'].rolling(window=long_window).mean()

        last_ma_short = historical_data['ma_short'].iloc[-1]
        last_ma_medium = historical_data['ma_medium'].iloc[-1]
        last_ma_long = historical_data['ma_long'].iloc[-1]

        if last_ma_short > last_ma_medium > last_ma_long:
            return 'BUY'
        elif last_ma_short < last_ma_medium < last_ma_long:
            return 'SELL'
        else:
            return 'HOLD'

    except Exception as e:
        print(f"An error occurred during 3MA calculation: {e}")
        return None

def calculate_performance_metrics(trade_history: List[Dict[str, Any]]) -> str:
    """
    Calculates and summarizes performance metrics from a list of trades.
    """
    if not trade_history:
        return "No trade history to analyze."

    df = pd.DataFrame(trade_history)
    total_trades = len(df)
    
    # The Alpaca API `get_orders` doesn't directly provide PnL for each trade.
    # This would require a more complex calculation involving fetching execution details (fills).
    # For this version, we will focus on metrics we can derive from the closed orders.
    
    winning_trades = len(df[df['status'] == 'filled']) # This is a simplification.
    losing_trades = len(df[df['status'] == 'canceled']) # This is not accurate.
    
    # A true win/loss calculation requires comparing entry and exit prices for pairs of trades.
    # This is a complex task. For now, we will report on completed trades.

    report = (
        "Performance Report:\n"
        f"- Total Closed Orders: {total_trades}\n"
        f"- Filled Orders: {winning_trades}\n"
        f"- Canceled/Rejected Orders: {losing_trades}\n"
        "Note: True PnL and win/loss ratio requires pairing buy/sell trades, which is a complex feature."
    )
    return report

def fetch_market_data(assets: List[str]) -> Dict[str, pd.DataFrame]:
    """Simulates fetching market data for a list of assets."""
    # This is a mock. In a real scenario, you'd use an API like Alpaca.
    print(f"Fetching market data for: {assets}")
    return {asset: pd.DataFrame({'close': [100, 102, 101]}) for asset in assets}

def filter_assets_by_volume(market_data: Dict[str, pd.DataFrame], min_volume: int = 10000) -> List[str]:
    """Simulates filtering assets based on trading volume."""
    # This is a mock. You'd calculate volume from the real market data.
    print(f"Filtering assets with volume > {min_volume}")
    return list(market_data.keys())
