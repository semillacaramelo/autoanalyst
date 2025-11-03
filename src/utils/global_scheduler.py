"""
Global Scheduler for Autonomous Trading
Enhanced with intelligent market rotation and adaptive intervals.
"""

import time
import logging
from datetime import datetime
import pytz
from typing import List, Optional
from src.config.settings import settings
from src.crew.orchestrator import trading_orchestrator
from src.utils.market_calendar import MarketCalendar
from src.utils.state_manager import StateManager
from src.connectors.alpaca_connector import alpaca_manager
from src.crew.market_rotation_strategy import market_rotation_strategy

logger = logging.getLogger(__name__)


class AutoTradingScheduler:
    """
    Autonomous 24/7 trading scheduler with intelligent market rotation.

    Features:
    - Time-based market selection (US equity during market hours)
    - Performance-based market rotation (switches to best performer)
    - Adaptive scan intervals (5min equity, 15min crypto peak, 30min off-peak)
    - Asset-class-aware strategy selection
    - Market activity monitoring
    """

    def __init__(self):
        self.market_calendar = MarketCalendar()
        self.state_manager = StateManager()
        self.orchestrator = trading_orchestrator
        self.market_rotation = market_rotation_strategy
        self.state = self.state_manager.load_state()

        # Adaptive interval configuration (in minutes)
        self.intervals = {
            "US_EQUITY": 5,  # Peak liquidity: scan every 5 minutes
            "CRYPTO_PEAK": 15,  # High activity: scan every 15 minutes
            "CRYPTO_OFFPEAK": 30,  # Low activity: scan every 30 minutes
            "FOREX": 10,  # Moderate: scan every 10 minutes
        }

    def _emergency_close_positions(self):
        """Emergency function to close all open positions."""
        try:
            positions = alpaca_manager.get_positions()
            for pos in positions:
                side = "sell" if pos["side"] == "long" else "buy"
                logger.warning(f"EMERGENCY: Closing position {pos['qty']} {pos['symbol']}")
                alpaca_manager.place_market_order(pos["symbol"], pos["qty"], side.upper())
        except Exception as e:
            logger.error(f"Failed to execute emergency position close: {e}", exc_info=True)

    def _calculate_next_interval(self, active_market: str, current_time: datetime) -> int:
        """
        Calculate adaptive sleep interval based on market and time.

        Strategy:
        - US_EQUITY: 5min (peak liquidity)
        - CRYPTO (peak hours 9-23 UTC): 15min
        - CRYPTO (off-peak 0-8 UTC): 30min
        - FOREX: 10min

        Args:
            active_market: Currently selected market
            current_time: Current UTC time

        Returns:
            Sleep duration in seconds
        """
        if active_market == "US_EQUITY":
            interval_minutes = self.intervals["US_EQUITY"]
        elif active_market == "CRYPTO":
            # Peak crypto hours: 9:00-23:00 UTC (highest trading volume)
            hour_utc = current_time.hour
            if 9 <= hour_utc < 23:
                interval_minutes = self.intervals["CRYPTO_PEAK"]
            else:
                interval_minutes = self.intervals["CRYPTO_OFFPEAK"]
        elif active_market == "FOREX":
            interval_minutes = self.intervals["FOREX"]
        else:
            # Fallback
            interval_minutes = settings.scan_interval_minutes

        logger.debug(f"Next interval for {active_market}: {interval_minutes} minutes")
        return interval_minutes * 60

    def _get_optimal_strategies(self, asset_class: str) -> List[str]:
        """
        Select optimal trading strategies for the given asset class.

        Args:
            asset_class: Market type (US_EQUITY, CRYPTO, FOREX)

        Returns:
            List of strategy names optimized for this asset class
        """
        # Strategy recommendations per asset class
        strategy_map = {
            "US_EQUITY": ["3ma", "rsi_breakout", "macd"],  # All strategies work well
            "CRYPTO": ["3ma", "rsi_breakout"],  # Trend-following best for crypto volatility
            "FOREX": ["macd", "bollinger"],  # Momentum strategies for forex
        }

        selected_strategies = strategy_map.get(asset_class, ["3ma"])
        logger.debug(f"Selected strategies for {asset_class}: {selected_strategies}")
        return selected_strategies

    def run_forever(self):
        """
        Main 24/7 loop for autonomous trading with intelligent market rotation.

        Flow:
        1. Select active market using intelligent rotation strategy
        2. Get optimal strategies for the selected market
        3. Execute trading cycle with market-aware configuration
        4. Update market performance metrics
        5. Calculate adaptive sleep interval
        6. Repeat
        """
        logger.info("Starting AutoTradingScheduler in 24/7 mode with intelligent market rotation.")
        logger.info(
            f"Configured intervals: US_EQUITY={self.intervals['US_EQUITY']}min, "
            f"CRYPTO_PEAK={self.intervals['CRYPTO_PEAK']}min, "
            f"CRYPTO_OFFPEAK={self.intervals['CRYPTO_OFFPEAK']}min, "
            f"FOREX={self.intervals['FOREX']}min"
        )

        while True:
            current_time_utc = datetime.now(pytz.utc)

            try:
                # Step 1: Intelligent market selection
                selected_market = self.market_rotation.select_active_market(
                    target_markets=settings.target_markets, consider_performance=True
                )

                logger.info(
                    f"[{current_time_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}] " f"Selected market: {selected_market}"
                )

                # Step 2: Get optimal strategies for this market
                optimal_strategies = self._get_optimal_strategies(selected_market)

                # Step 3: Check if market is actually open
                active_markets = self.market_calendar.get_active_markets(current_time_utc, [selected_market])

                if not active_markets:
                    # Market not open (shouldn't happen with rotation logic, but safety check)
                    next_open = self.market_calendar.next_market_open([selected_market])
                    if next_open:
                        sleep_duration = (next_open - current_time_utc).total_seconds()
                        sleep_chunk = min(sleep_duration, 3600)
                        logger.info(
                            f"{selected_market} not open. Sleeping {sleep_chunk/60:.2f} min "
                            f"(next open: {next_open.strftime('%Y-%m-%d %H:%M:%S %Z')})."
                        )
                        time.sleep(sleep_chunk)
                    else:
                        logger.warning(f"No schedule found for {selected_market}. Sleeping 1 hour.")
                        time.sleep(3600)
                    continue

                # Step 4: Execute trading cycle
                logger.info(
                    f"Starting trading cycle for {selected_market} " f"with strategies: {', '.join(optimal_strategies)}"
                )

                cycle_start_time = time.time()

                try:
                    # Run orchestrator with market-specific configuration
                    # Note: This assumes orchestrator can be configured per-run
                    # In practice, you may need to modify orchestrator to accept market parameter
                    self.orchestrator.run_cycle()

                    cycle_duration = time.time() - cycle_start_time
                    logger.info(f"Trading cycle completed in {cycle_duration:.2f}s")

                    # Step 5: Update market performance
                    # Note: Performance tracking would be done within orchestrator/execution
                    # This is a placeholder for future integration

                except Exception as e:
                    logger.error(f"Critical error in trading cycle: {e}", exc_info=True)
                    if settings.auto_close_on_error:
                        logger.warning("Auto-closing all positions due to critical error.")
                        self._emergency_close_positions()

                # Step 6: Save state after each cycle
                self.state["last_run_timestamp"] = current_time_utc.isoformat()
                self.state["active_market"] = selected_market
                self.state["strategies_used"] = optimal_strategies

                try:
                    positions = alpaca_manager.get_positions()
                    self.state["positions"] = positions
                    self.state["daily_pnl"] = sum(p.get("unrealized_pl", 0.0) for p in positions)
                except Exception as e:
                    logger.warning(f"Failed to update position state: {e}")

                self.state_manager.save_state(self.state)

                # Step 7: Calculate adaptive interval and sleep
                interval = self._calculate_next_interval(selected_market, current_time_utc)

                # Log market rotation stats
                rotation_stats = self.market_rotation.get_market_statistics()
                logger.info(
                    f"Market rotation stats: {rotation_stats['rotation_count']} rotations, "
                    f"last: {rotation_stats['last_rotation']}"
                )

                logger.info(f"Cycle complete. Sleeping for {interval/60:.2f} minutes until next scan.")
                time.sleep(interval)

            except KeyboardInterrupt:
                logger.info("Received shutdown signal. Stopping scheduler gracefully.")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
                # Sleep for a safe interval on error
                logger.info("Sleeping for 5 minutes after error before retry.")
                time.sleep(300)

        logger.info("AutoTradingScheduler stopped.")
