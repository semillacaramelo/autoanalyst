"""
Backtesting Engine V2 - Event-Driven
"""

import numpy as np
from typing import List, Dict, Optional
from src.connectors.alpaca_connector import alpaca_manager
from src.strategies.registry import get_strategy
from src.config.settings import settings
import logging
import re

logger = logging.getLogger(__name__)


class BacktesterV2:
    def __init__(self, start_date: str, end_date: str, risk_free_rate=0.02):
        self.start_date = start_date
        self.end_date = end_date
        self.risk_free_rate = risk_free_rate

    def _get_annualization_factor(self, timeframe: str) -> int:
        """Determines the annualization factor based on the timeframe."""
        timeframe_lower = timeframe.lower()
        match = re.match(r"(\d+)\s*(m|min|h|hour|d|day)", timeframe_lower)
        if not match:
            return 252  # Default to daily

        unit_str = match.group(2)
        if "m" in unit_str:
            return 252 * 6.5 * 60  # Daily * hours * minutes
        elif "h" in unit_str:
            return 252 * 6.5  # Daily * hours
        elif "d" in unit_str:
            return 252
        return 252

    def run(
        self,
        symbol: str,
        strategy_name: str,
        timeframe: str = "1Day",
        slippage_percent: float = 0.001,
        commission_per_trade: float = 1.0,
        data_feed: Optional[str] = None,
    ) -> Dict:
        """Run a backtest for a single strategy."""
        # Use configured data feed if not explicitly provided
        if data_feed is None:
            data_feed = settings.alpaca_data_feed

        strategy = get_strategy(strategy_name)

        data = alpaca_manager.fetch_historical_bars(symbol, timeframe, start=self.start_date, end=self.end_date)

        if data.empty:
            logger.warning(f"No data found for {symbol} in the given date range.")
            return self.calculate_performance([], timeframe)

        trades = []
        position = 0

        # Event-driven loop
        for i in range(1, len(data)):
            # On each bar, the strategy only sees data up to that point
            df_slice = data.iloc[0:i]

            if len(df_slice) < strategy.min_bars_required:
                continue

            signal = strategy.generate_signal(df_slice)
            validated_signal = strategy.validate_signal(df_slice, signal, data_feed)

            if validated_signal["signal"] == "BUY" and position == 0:
                price = data["close"].iloc[i] * (1 + slippage_percent)
                trades.append(
                    {"date": data.index[i], "type": "BUY", "price": price, "commission": commission_per_trade}
                )
                position = 1
            elif validated_signal["signal"] == "SELL" and position == 1:
                price = data["close"].iloc[i] * (1 - slippage_percent)
                trades.append(
                    {"date": data.index[i], "type": "SELL", "price": price, "commission": commission_per_trade}
                )
                position = 0

        return self.calculate_performance(trades, timeframe)

    def compare(self, symbol: str, strategy_names: List[str], timeframe: str = "1Day") -> Dict:
        """Compare the performance of multiple strategies."""
        results = {}
        for name in strategy_names:
            results[name] = self.run(symbol, name, timeframe)
        return results

    def calculate_performance(self, trades: List[Dict], timeframe: str) -> Dict:
        """Calculate performance metrics from a list of trades."""
        annualization_factor = self._get_annualization_factor(timeframe)

        if not trades:
            return {
                "trades": 0,
                "pnl": 0,
                "win_rate": 0,
                "sharpe_ratio": 0,
                "sortino_ratio": 0,
                "calmar_ratio": 0,
                "max_drawdown": 0,
            }

        # Count complete trade pairs (BUY-SELL)
        num_complete_trades = len(trades) // 2

        if len(trades) % 2 != 0:
            logger.info(
                "Open position detected (%d trades). Calculating metrics for %d completed trades.",
                len(trades),
                num_complete_trades,
            )
            if num_complete_trades == 0:
                return {
                    "trades": 0,
                    "pnl": 0,
                    "win_rate": 0,
                    "sharpe_ratio": 0,
                    "sortino_ratio": 0,
                    "calmar_ratio": 0,
                    "max_drawdown": 0,
                    "note": "No completed trades (1 open position)",
                }
            # Use only complete pairs for calculation
            trades = trades[: num_complete_trades * 2]

        pnl = 0
        wins = 0
        returns = []
        trade_pnls = []

        for i in range(0, len(trades), 2):
            buy_trade = trades[i]
            sell_trade = trades[i + 1]
            trade_pnl = (sell_trade["price"] - buy_trade["price"]) - (
                buy_trade["commission"] + sell_trade["commission"]
            )
            trade_pnls.append(trade_pnl)
            pnl += trade_pnl
            if trade_pnl > 0:
                wins += 1
            returns.append((sell_trade["price"] / buy_trade["price"]) - 1)

        returns = np.array(returns)
        total_trades = len(trades) // 2
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0

        # Sharpe Ratio
        if np.std(returns) > 0:
            sharpe_ratio = (np.mean(returns) * annualization_factor - self.risk_free_rate) / (
                np.std(returns) * np.sqrt(annualization_factor)
            )
        else:
            sharpe_ratio = 0

        # Sortino Ratio
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 1 and np.std(downside_returns) > 0:
            sortino_ratio = (np.mean(returns) * annualization_factor - self.risk_free_rate) / (
                np.std(downside_returns) * np.sqrt(annualization_factor)
            )
        else:
            sortino_ratio = 0

        # Max Drawdown & Calmar Ratio
        cumulative_pnl = np.cumsum(trade_pnls)
        peak = np.maximum.accumulate(cumulative_pnl)
        drawdown = cumulative_pnl - peak
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0

        # Calmar Ratio
        annualized_return = np.mean(returns) * annualization_factor
        if max_drawdown < 0:
            calmar_ratio = annualized_return / abs(max_drawdown)
        else:
            calmar_ratio = 0

        return {
            "trades": total_trades,
            "pnl": round(pnl, 2),
            "win_rate": round(win_rate, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "sortino_ratio": round(sortino_ratio, 2),
            "calmar_ratio": round(calmar_ratio, 2),
            "max_drawdown": round(max_drawdown, 2),
        }


backtester_v2 = BacktesterV2(start_date="2024-01-01", end_date="2024-06-30")  # Default dates
