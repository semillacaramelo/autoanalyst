"""
Backtesting Engine
"""
import pandas as pd
from typing import List, Dict
from src.connectors.alpaca_connector import alpaca_manager
from src.strategies.registry import get_strategy
import logging

logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date

    def run(self, symbol: str, strategy_name: str, timeframe: str = '1Day') -> Dict:
        """Run a backtest for a single strategy."""
        strategy = get_strategy(strategy_name)

        # Fetch data for the entire period
        # Note: This is a simplified backtester. A real one would use a more robust
        # data fetching and slicing mechanism.
        data = alpaca_manager.fetch_historical_bars(symbol, timeframe, limit=1000) # Fetch more data to ensure enough for the start date
        data = data[self.start_date:self.end_date]

        trades = []
        position = 0 # 1 for long, -1 for short, 0 for flat

        for i in range(strategy.min_bars_required, len(data)):
            df_slice = data.iloc[:i]
            signal = strategy.generate_signal(df_slice)
            validated_signal = strategy.validate_signal(df_slice, signal)

            if validated_signal['signal'] == 'BUY' and position == 0:
                trades.append({'date': data.index[i], 'type': 'BUY', 'price': data['close'].iloc[i]})
                position = 1
            elif validated_signal['signal'] == 'SELL' and position == 1:
                trades.append({'date': data.index[i], 'type': 'SELL', 'price': data['close'].iloc[i]})
                position = 0

        return self.calculate_performance(trades, data['close'].iloc[-1])

    def compare(self, symbol: str, strategy_names: List[str], timeframe: str = '1Day') -> Dict:
        """Compare the performance of multiple strategies."""
        results = {}
        for name in strategy_names:
            results[name] = self.run(symbol, name, timeframe)
        return results

    def calculate_performance(self, trades: List[Dict], final_price: float) -> Dict:
        """Calculate performance metrics from a list of trades."""
        if not trades:
            return {"trades": 0, "pnl": 0, "win_rate": 0}

        pnl = 0
        wins = 0
        for i in range(0, len(trades) - 1, 2):
            buy_trade = trades[i]
            sell_trade = trades[i+1]
            trade_pnl = sell_trade['price'] - buy_trade['price']
            pnl += trade_pnl
            if trade_pnl > 0:
                wins += 1

        total_trades = len(trades) // 2
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0

        return {
            "trades": total_trades,
            "pnl": round(pnl, 2),
            "win_rate": round(win_rate, 2)
        }

backtester = Backtester(start_date="2024-01-01", end_date="2024-06-30") # Default dates
