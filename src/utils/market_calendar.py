"""
Market Calendar
Tracks global market hours to determine when the trading system should be active.
"""
from datetime import datetime, time
from typing import List
import pytz

class MarketCalendar:
    """Tracks global market hours."""

    MARKETS = {
        "US_EQUITY": {"open": time(9, 30), "close": time(16, 0), "tz": "America/New_York"},
        "EU_EQUITY": {"open": time(8, 0), "close": time(16, 30), "tz": "Europe/London"},
        "CRYPTO": {"open": time(0, 0), "close": time(23, 59, 59), "tz": "UTC"},  # 24/7
    }

    def get_active_markets(self, timestamp: datetime, target_markets: List[str]) -> List[str]:
        """Return list of currently open markets from the target list."""
        active_markets = []
        for market_name in target_markets:
            if market_name in self.MARKETS:
                market = self.MARKETS[market_name]
                tz = pytz.timezone(market["tz"])
                local_time = timestamp.astimezone(tz).time()

                if market["open"] <= local_time <= market["close"]:
                    active_markets.append(market_name)
        return active_markets

    def next_market_open(self, target_markets: List[str]) -> datetime:
        """Find the next market opening time across all target markets."""
        now = datetime.now(pytz.utc)
        next_opens = []

        for market_name in target_markets:
            if market_name in self.MARKETS:
                market = self.MARKETS[market_name]
                tz = pytz.timezone(market["tz"])
                market_open_time = market["open"]

                now_local = now.astimezone(tz)
                today_open = now_local.replace(hour=market_open_time.hour, minute=market_open_time.minute, second=0, microsecond=0)

                if now_local.time() < market_open_time:
                    next_opens.append(today_open)
                else:
                    # It's already past opening time today, so check tomorrow
                    tomorrow = now_local + pytz.timedelta(days=1)
                    tomorrow_open = tomorrow.replace(hour=market_open_time.hour, minute=market_open_time.minute, second=0, microsecond=0)
                    next_opens.append(tomorrow_open)

        return min(next_opens) if next_opens else None
