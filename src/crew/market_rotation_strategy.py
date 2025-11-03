"""
Market Rotation Strategy
Intelligently selects the best market to trade based on time and performance.

This module implements a hybrid approach:
1. Time-based: Prioritize US equity during market hours (best liquidity)
2. Performance-based: Track win rates and profitability per market
3. Adaptive: Automatically switch to crypto when US markets are closed
"""

from datetime import datetime
from typing import List, Dict, Optional
import pytz
import logging
from src.utils.market_calendar import MarketCalendar
from src.utils.state_manager import StateManager
from pathlib import Path

logger = logging.getLogger(__name__)


class MarketRotationStrategy:
    """
    Intelligent market selection based on time and performance.

    Priority Logic:
    1. US market hours (9:30-4:00 ET) → US_EQUITY (best liquidity)
    2. US market closed → Evaluate CRYPTO vs next US open
    3. Performance overlay: Adjust based on recent market performance
    """

    def __init__(self, state_file: Optional[Path] = None):
        """
        Initialize market rotation strategy.

        Args:
            state_file: Path to state file for performance tracking (default: data/market_rotation_state.json)
        """
        self.market_calendar = MarketCalendar()
        self.state_manager = StateManager(state_file or Path("data/market_rotation_state.json"))
        self.performance_state = self._load_performance_state()

    def _load_performance_state(self) -> Dict:
        """
        Load market performance state from disk.

        Returns:
            Dictionary with market performance metrics
        """
        state = self.state_manager.load_state()

        # Initialize default structure if empty
        if not state:
            state = {
                "market_performance": {
                    "US_EQUITY": {"trades": 0, "wins": 0, "total_profit": 0.0, "last_update": None},
                    "CRYPTO": {"trades": 0, "wins": 0, "total_profit": 0.0, "last_update": None},
                    "FOREX": {"trades": 0, "wins": 0, "total_profit": 0.0, "last_update": None},
                },
                "last_rotation": None,
                "rotation_count": 0,
            }
            self.state_manager.save_state(state)

        return state

    def select_active_market(
        self, target_markets: Optional[List[str]] = None, consider_performance: bool = True
    ) -> str:
        """
        Select the best market to trade right now.

        Args:
            target_markets: List of markets to consider (default: ['US_EQUITY', 'CRYPTO'])
            consider_performance: Whether to factor in performance metrics

        Returns:
            Selected market name ('US_EQUITY', 'CRYPTO', or 'FOREX')
        """
        if target_markets is None:
            target_markets = ["US_EQUITY", "CRYPTO"]

        now = datetime.now(pytz.utc)

        # Step 1: Get currently open markets
        active_markets = self.market_calendar.get_active_markets(now, target_markets)

        logger.info(f"Active markets at {now}: {active_markets}")

        # Step 2: Time-based priority
        if "US_EQUITY" in active_markets and "US_EQUITY" in target_markets:
            # US market is open - highest priority due to liquidity
            selected = "US_EQUITY"
            reason = "US market hours (best liquidity)"
        elif "CRYPTO" in target_markets:
            # US market closed - default to crypto (24/7)
            selected = "CRYPTO"
            reason = "US market closed, crypto 24/7"
        elif "FOREX" in target_markets and "FOREX" in active_markets:
            # Forex market open
            selected = "FOREX"
            reason = "Forex market hours"
        else:
            # Fallback
            selected = target_markets[0] if target_markets else "US_EQUITY"
            reason = "Default fallback"

        # Step 3: Performance overlay (if enabled)
        if consider_performance and len(active_markets) > 1:
            performance_adjustment = self._evaluate_performance(active_markets)
            if performance_adjustment:
                logger.info(f"Performance suggests: {performance_adjustment}")
                # Only override if performance difference is significant
                performance_score = self._calculate_market_score(performance_adjustment)
                current_score = self._calculate_market_score(selected)

                if performance_score > current_score * 1.2:  # 20% better
                    selected = performance_adjustment
                    reason = f"Performance-based override (score: {performance_score:.2f} vs {current_score:.2f})"

        logger.info(f"Selected market: {selected} ({reason})")

        # Update rotation tracking
        self._track_rotation(selected)

        return selected

    def _evaluate_performance(self, active_markets: List[str]) -> Optional[str]:
        """
        Evaluate performance metrics to suggest best market.

        Args:
            active_markets: List of currently active markets

        Returns:
            Market name with best performance, or None
        """
        performance = self.performance_state.get("market_performance", {})

        best_market = None
        best_score = 0.0

        for market in active_markets:
            if market in performance:
                score = self._calculate_market_score(market)
                logger.debug(f"{market} performance score: {score:.2f}")

                if score > best_score:
                    best_score = score
                    best_market = market

        # Only suggest if we have enough data (at least 5 trades)
        if best_market and performance[best_market]["trades"] >= 5:
            return best_market

        return None

    def _calculate_market_score(self, market: str) -> float:
        """
        Calculate performance score for a market.

        Formula: win_rate × avg_profit × log(trade_count + 1)

        Args:
            market: Market name

        Returns:
            Performance score (higher is better)
        """
        performance = self.performance_state.get("market_performance", {})

        if market not in performance:
            return 0.0

        metrics = performance[market]
        trades = metrics.get("trades", 0)
        wins = metrics.get("wins", 0)
        total_profit = metrics.get("total_profit", 0.0)

        if trades == 0:
            return 0.0

        win_rate = wins / trades
        avg_profit = total_profit / trades

        # Log scaling for trade count (diminishing returns)
        import math

        trade_factor = math.log(trades + 1)

        score = win_rate * avg_profit * trade_factor

        return max(0.0, score)

    def _track_rotation(self, selected_market: str):
        """
        Track market rotation for monitoring.

        Args:
            selected_market: The market that was selected
        """
        now = datetime.now(pytz.utc)
        last_rotation = self.performance_state.get("last_rotation")

        # Only increment if we actually rotated
        if last_rotation != selected_market:
            self.performance_state["rotation_count"] = self.performance_state.get("rotation_count", 0) + 1
            logger.info(
                f"Market rotation: {last_rotation} → {selected_market} (rotation #{self.performance_state['rotation_count']})"
            )

        self.performance_state["last_rotation"] = selected_market
        self.performance_state["last_rotation_time"] = now.isoformat()

        self.state_manager.save_state(self.performance_state)

    def update_market_performance(self, market: str, trade_result: Dict):
        """
        Update performance metrics for a market after a trade.

        Args:
            market: Market name ('US_EQUITY', 'CRYPTO', 'FOREX')
            trade_result: Dictionary with trade outcome
                {
                    'success': bool,
                    'profit': float,
                    'symbol': str,
                    'strategy': str,
                    'timestamp': str
                }
        """
        if "market_performance" not in self.performance_state:
            self.performance_state["market_performance"] = {}

        if market not in self.performance_state["market_performance"]:
            self.performance_state["market_performance"][market] = {
                "trades": 0,
                "wins": 0,
                "total_profit": 0.0,
                "last_update": None,
            }

        metrics = self.performance_state["market_performance"][market]

        # Update metrics
        metrics["trades"] += 1
        if trade_result.get("success", False):
            metrics["wins"] += 1
        metrics["total_profit"] += trade_result.get("profit", 0.0)
        metrics["last_update"] = trade_result.get("timestamp", datetime.now(pytz.utc).isoformat())

        # Calculate derived metrics
        metrics["win_rate"] = metrics["wins"] / metrics["trades"] if metrics["trades"] > 0 else 0.0
        metrics["avg_profit"] = metrics["total_profit"] / metrics["trades"] if metrics["trades"] > 0 else 0.0

        logger.info(
            f"Updated {market} performance: {metrics['trades']} trades, "
            f"{metrics['win_rate']:.1%} win rate, "
            f"${metrics['avg_profit']:.2f} avg profit"
        )

        # Save state
        self.state_manager.save_state(self.performance_state)

    def get_market_statistics(self) -> Dict:
        """
        Get comprehensive statistics for all markets.

        Returns:
            Dictionary with market statistics
        """
        stats = {
            "markets": {},
            "rotation_count": self.performance_state.get("rotation_count", 0),
            "last_rotation": self.performance_state.get("last_rotation"),
            "last_rotation_time": self.performance_state.get("last_rotation_time"),
        }

        performance = self.performance_state.get("market_performance", {})

        for market, metrics in performance.items():
            stats["markets"][market] = {
                "trades": metrics.get("trades", 0),
                "wins": metrics.get("wins", 0),
                "win_rate": metrics.get("win_rate", 0.0),
                "total_profit": metrics.get("total_profit", 0.0),
                "avg_profit": metrics.get("avg_profit", 0.0),
                "score": self._calculate_market_score(market),
                "last_update": metrics.get("last_update"),
            }

        return stats

    def reset_performance(self, market: Optional[str] = None):
        """
        Reset performance metrics (for testing or new periods).

        Args:
            market: Specific market to reset, or None for all markets
        """
        if market:
            if market in self.performance_state.get("market_performance", {}):
                self.performance_state["market_performance"][market] = {
                    "trades": 0,
                    "wins": 0,
                    "total_profit": 0.0,
                    "last_update": None,
                }
                logger.info(f"Reset performance for {market}")
        else:
            self.performance_state["market_performance"] = {
                "US_EQUITY": {"trades": 0, "wins": 0, "total_profit": 0.0, "last_update": None},
                "CRYPTO": {"trades": 0, "wins": 0, "total_profit": 0.0, "last_update": None},
                "FOREX": {"trades": 0, "wins": 0, "total_profit": 0.0, "last_update": None},
            }
            self.performance_state["rotation_count"] = 0
            logger.info("Reset performance for all markets")

        self.state_manager.save_state(self.performance_state)


# Global singleton instance
market_rotation_strategy = MarketRotationStrategy()
