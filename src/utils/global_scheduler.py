from datetime import datetime
import time
import logging
from src.utils.market_calendar import MarketCalendar
from src.utils.state_manager import StateManager
from main import TradingOrchestrator
from src.config.settings import settings

logger = logging.getLogger(__name__)

class AutoTradingScheduler:
    def __init__(self):
        self.market_calendar = MarketCalendar()
        self.state_manager = StateManager()
        self.orchestrator = TradingOrchestrator()

    def run_forever(self):
        """Main 24/7 loop"""
        while True:
            current_time = datetime.now()
            active_markets = self.market_calendar.get_active_markets(current_time)
            if not active_markets:
                next_open = self.market_calendar.next_market_open()
                sleep_duration = (next_open - current_time).total_seconds()
                logger.info(f"All markets closed. Sleeping until {next_open}")
                time.sleep(min(sleep_duration, 3600))
                continue
            try:
                self.orchestrator.run_cycle()
            except Exception as e:
                logger.error(f"Cycle failed: {e}", exc_info=True)
                if settings.auto_close_on_error:
                    self.emergency_close_positions()
            self.state_manager.save_state({
                "last_run": current_time,
                "positions": self.get_current_positions(),
                "daily_pnl": self.calculate_daily_pnl()
            })
            interval = self.calculate_next_interval()
            time.sleep(interval)

    def emergency_close_positions(self):
        logger.warning("Emergency: Closing all positions (stub).")

    def get_current_positions(self):
        return {}

    def calculate_daily_pnl(self):
        return 0.0

    def calculate_next_interval(self):
        # Placeholder: adaptive interval logic
        return settings.scan_interval_minutes * 60 if not getattr(settings, "adaptive_interval", False) else 60
