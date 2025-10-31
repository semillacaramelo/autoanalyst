"""
Parallel Execution Orchestrator
"""
import time
import logging
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List
from src.config.settings import settings
from src.crew.market_scanner_crew import market_scanner_crew
from src.crew.trading_crew import TradingCrew

logger = logging.getLogger(__name__)

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


class TradingOrchestrator:
    def __init__(self):
        self.market_scanner = market_scanner_crew
        self.active_crews: Dict[str, TradingCrew] = {}
        self.global_rate_limiter = GlobalRateLimiter()
        self.executor = ThreadPoolExecutor(max_workers=3)  # Parallel crews

    def _run_trading_crew(self, symbol: str, strategy: str):
        """Wrapper to run a single trading crew."""
        try:
            # Each thread needs its own TradingCrew instance
            trading_crew_instance = TradingCrew()
            return trading_crew_instance.run(symbol=symbol, strategy=strategy)
        except Exception as e:
            logger.error(f"Error running trading crew for {symbol} ({strategy}): {e}", exc_info=True)
            return {"success": False, "symbol": symbol, "strategy": strategy, "error": str(e)}

    def run_cycle(self):
        """Single trading cycle with parallel execution."""
        logger.info("Starting new trading cycle.")

        # Step 1: Scan market
        logger.info("Running market scanner...")
        scan_results = self.market_scanner.run()
        # The output from the crew is a string, so we need to parse it.
        # This is a temporary solution until the output is structured.
        top_assets = self._parse_scan_results(scan_results)

        if not top_assets:
            logger.warning("Market scanner returned no assets. Ending cycle.")
            return

        # Step 2: Distribute work across parallel crews
        futures = []
        for asset_config in top_assets[:3]:  # Top 3
            for strategy in asset_config.get("recommended_strategies", ["3ma"]):
                if self.global_rate_limiter.can_start_crew():
                    logger.info(f"Submitting trading crew for {asset_config['symbol']} with strategy {strategy}")
                    future = self.executor.submit(
                        self._run_trading_crew,
                        symbol=asset_config["symbol"],
                        strategy=strategy
                    )
                    futures.append(future)
                else:
                    logger.warning("Rate limit budget reached. Cannot start more crews this cycle.")
                    break
            if not self.global_rate_limiter.can_start_crew():
                break

        # Step 3: Wait for all crews to complete
        results = [f.result() for f in futures]

        # Step 4: Aggregate and log results
        self.log_cycle_summary(results)

    def _parse_scan_results(self, scan_results_str: str) -> List[Dict]:
        """Parses the string output of the scanner crew into a list of assets."""
        import json
        try:
            # A simple heuristic to find the JSON blob in the output
            if "```json" in scan_results_str:
                json_str = scan_results_str.split("```json")[1].split("```")[0]
            else:
                json_str = scan_results_str

            data = json.loads(json_str)
            return data.get("top_assets", [])
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse market scanner output: {e}")
            logger.debug(f"Raw scanner output:\n{scan_results_str}")
            return []

    def log_cycle_summary(self, results: List[Dict]):
        """Logs the summary of the trading cycle."""
        logger.info("Trading cycle finished. Summary:")
        for res in results:
            if res.get("success"):
                logger.info(f"  - SUCCESS: {res['symbol']} ({res['strategy']}). Result: {res.get('result')}")
            else:
                logger.error(f"  - FAILED: {res['symbol']} ({res['strategy']}). Error: {res.get('error')}")

trading_orchestrator = TradingOrchestrator()
