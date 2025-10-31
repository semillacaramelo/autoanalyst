from datetime import datetime, time, timedelta
import pytz

class MarketCalendar:
    """Tracks global market hours"""

    MARKETS = {
        "US_EQUITY": {"open": time(9, 30), "close": time(16, 0), "tz": "America/New_York"},
        "EU_EQUITY": {"open": time(8, 0), "close": time(16, 30), "tz": "Europe/London"},
        "CRYPTO": {"open": time(0, 0), "close": time(23, 59), "tz": "UTC"},
    }

    def get_active_markets(self, timestamp: datetime):
        active = []
        for name, info in self.MARKETS.items():
            tz = pytz.timezone(info["tz"])
            local_time = timestamp.astimezone(tz).time()
            if info["open"] <= local_time <= info["close"]:
                active.append(name)
        return active

    def next_market_open(self):
        now = datetime.utcnow()
        soonest = None
        soonest_time = None
        for name, info in self.MARKETS.items():
            tz = pytz.timezone(info["tz"])
            local_now = now.astimezone(tz)
            open_dt = local_now.replace(hour=info["open"].hour, minute=info["open"].minute, second=0, microsecond=0)
            if local_now.time() > info["close"]:
                open_dt += timedelta(days=1)
            if soonest_time is None or open_dt < soonest_time:
                soonest = open_dt
                soonest_time = open_dt
        return soonest_time
