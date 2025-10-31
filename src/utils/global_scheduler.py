"""
Global Scheduler for Autonomous Trading
"""
import time
import logging
from datetime import datetime
import pytz
from src.config.settings import settings
from src.crew.orchestrator import trading_orchestrator
from src.utils.market_calendar import MarketCalendar
from src.utils.state_manager import StateManager
from src.connectors.alpaca_connector import alpaca_manager

logger = logging.getLogger(__name__)

class AutoTradingScheduler:
    def __init__(self):
        self.market_calendar = MarketCalendar()
        self.state_manager = StateManager()
        self.orchestrator = trading_orchestrator
        self.state = self.state_manager.load_state()

    def _emergency_close_positions(self):
        """Emergency function to close all open positions."""
        try:
            positions = alpaca_manager.get_positions()
            for pos in positions:
                side = "sell" if pos['side'] == "long" else "buy"
                logger.warning(f"EMERGENCY: Closing position {pos['qty']} {pos['symbol']}")
                alpaca_manager.place_market_order(pos['symbol'], pos['qty'], side.upper())
        except Exception as e:
            logger.error(f"Failed to execute emergency position close: {e}", exc_info=True)

    def _calculate_next_interval(self) -> int:
        """Calculates the sleep interval before the next run."""
        # This is a placeholder for a more intelligent adaptive interval
        return settings.scan_interval_minutes * 60

    def run_forever(self):
        """Main 24/7 loop for the autonomous trading system."""
        logger.info("Starting AutoTradingScheduler in 24/7 mode.")
<<<<<<< HEAD

        while True:
            current_time_utc = datetime.now(pytz.utc)

            # Check if any target market is open
            active_markets = self.market_calendar.get_active_markets(current_time_utc, settings.target_markets)

=======

        while True:
            current_time_utc = datetime.now(pytz.utc)

            # Check if any target market is open
            active_markets = self.market_calendar.get_active_markets(current_time_utc, settings.target_markets)

>>>>>>> 4fa32c2 (Apply patch /tmp/fa19928c-52d8-47c4-91a0-d51264a9e589.patch)
            if not active_markets:
                next_open = self.market_calendar.next_market_open(settings.target_markets)
                if next_open:
                    sleep_duration = (next_open - current_time_utc).total_seconds()
                    # Sleep until the next market open, but wake up periodically
<<<<<<< HEAD
                    sleep_chunk = min(sleep_duration, 3600)
=======
                    sleep_chunk = min(sleep_duration, 3600)
>>>>>>> 4fa32c2 (Apply patch /tmp/fa19928c-52d8-47c4-91a0-d51264a9e589.patch)
                    logger.info(f"All target markets are closed. Sleeping for {sleep_chunk/60:.2f} minutes until next check (next open: {next_open.strftime('%Y-%m-%d %H:%M:%S %Z')}).")
                    time.sleep(sleep_chunk)
                else:
                    logger.warning("No target markets configured or found. Sleeping for 1 hour.")
                    time.sleep(3600)
                continue
<<<<<<< HEAD

=======

>>>>>>> 4fa32c2 (Apply patch /tmp/fa19928c-52d8-47c4-91a0-d51264a9e589.patch)
            logger.info(f"Active markets detected: {active_markets}. Starting trading cycle.")
            try:
                self.orchestrator.run_cycle()
            except Exception as e:
                logger.error(f"A critical error occurred in the trading cycle: {e}", exc_info=True)
                if settings.auto_close_on_error:
                    logger.warning("Auto-closing all positions due to critical error.")
                    self._emergency_close_positions()
<<<<<<< HEAD

=======

>>>>>>> 4fa32c2 (Apply patch /tmp/fa19928c-52d8-47c4-91a0-d51264a9e589.patch)
            # Save state after each cycle
            self.state['last_run_timestamp'] = current_time_utc
            self.state['positions'] = alpaca_manager.get_positions()
            # P&L calculation would be more complex, this is a placeholder
            self.state['daily_pnl'] = sum(p['unrealized_pl'] for p in self.state['positions'])
            self.state_manager.save_state(self.state)
<<<<<<< HEAD

=======

>>>>>>> 4fa32c2 (Apply patch /tmp/fa19928c-52d8-47c4-91a0-d51264a9e589.patch)
            interval = self._calculate_next_interval()
            logger.info(f"Cycle complete. Sleeping for {interval/60:.2f} minutes.")
            time.sleep(interval)
