"""
Global Rate Limiter
"""
import time
from collections import deque
from src.config.settings import settings

class GlobalRateLimiter:
    """Coordinates API usage across all parallel crews."""

    def __init__(self):
        self.gemini_rpm_budget = settings.rate_limit_rpm * 0.8  # 80% utilization
        self.alpaca_rpm_budget = 180  # 90% of 200 limit

        self.gemini_rpm_used = deque()
        self.alpaca_rpm_used = deque()

    def _cleanup(self):
        now = time.time()
        while self.gemini_rpm_used and now - self.gemini_rpm_used[0] > 60:
            self.gemini_rpm_used.popleft()
        while self.alpaca_rpm_used and now - self.alpaca_rpm_used[0] > 60:
            self.alpaca_rpm_used.popleft()

    def can_start_crew(self) -> bool:
        """Check if starting a new crew would exceed budgets."""
        self._cleanup()
        # Estimate: each crew uses ~14 Gemini calls, ~10 Alpaca calls
        projected_gemini = len(self.gemini_rpm_used) + 14
        projected_alpaca = len(self.alpaca_rpm_used) + 10

        return (projected_gemini < self.gemini_rpm_budget and
                projected_alpaca < self.alpaca_rpm_budget)

    def register_api_call(self, service: str):
        """Record an API call for rate limiting."""
        now = time.time()
        if service == 'gemini':
            self.gemini_rpm_used.append(now)
        elif service == 'alpaca':
            self.alpaca_rpm_used.append(now)

global_rate_limiter = GlobalRateLimiter()
