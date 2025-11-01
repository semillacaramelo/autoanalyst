"""
Trading Orchestrator - Parallel Crew Execution Manager

This module coordinates the execution of multiple trading crews in parallel.
It manages the complete trading cycle from market scanning to trade execution.

Workflow:
    1. Market Scanning: Run market scanner crew to identify opportunities
    2. Work Distribution: Submit trading crews for top assets/strategies
    3. Parallel Execution: Execute multiple crews concurrently (max 3)
    4. Result Aggregation: Collect and log results from all crews

Key Features:
    - Thread pool execution for parallel crew runs
    - Thread-safe rate limiting via GeminiConnectionManager
    - Automatic error recovery and logging
    - Configurable parallel execution limits

Usage:
    from src.crew.orchestrator import trading_orchestrator

    # Run a complete trading cycle
    trading_orchestrator.run_cycle()
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List
from src.crew.market_scanner_crew import market_scanner_crew
from src.crew.trading_crew import TradingCrew

logger = logging.getLogger(__name__)


class TradingOrchestrator:
    """
    Orchestrates parallel execution of trading crews.

    Manages the complete trading workflow including market scanning,
    crew distribution, parallel execution, and result aggregation.

    Attributes:
        market_scanner: Market scanner crew instance
        active_crews: Dictionary tracking active trading crew instances
        executor: Thread pool executor for parallel crew execution (max 3 workers)
    """

    def __init__(self):
        self.market_scanner = market_scanner_crew
        self.active_crews: Dict[str, TradingCrew] = {}
        self.executor = ThreadPoolExecutor(max_workers=3)  # Limit parallel crews to 3

    def _run_trading_crew(self, symbol: str, strategy: str):
        """
        Execute a single trading crew in a thread-safe manner.

        Each thread gets its own TradingCrew instance to avoid shared state issues.

        Args:
            symbol: Stock symbol to trade
            strategy: Trading strategy to apply

        Returns:
            dict: Execution result with success status, symbol, strategy, and result/error
        """
        try:
            # Create a new TradingCrew instance for this thread to avoid state conflicts
            trading_crew_instance = TradingCrew()
            return trading_crew_instance.run(symbol=symbol, strategy=strategy)
        except Exception as e:
            logger.error(
                f"Error running trading crew for {symbol} ({strategy}): {e}",
                exc_info=True,
            )
            return {
                "success": False,
                "symbol": symbol,
                "strategy": strategy,
                "error": str(e),
            }

    def run_cycle(self):
        """
        Execute a complete trading cycle with parallel crew execution.

        Workflow:
            1. Run market scanner to identify top trading opportunities
            2. Parse scanner results to get asset configurations
            3. Submit trading crews for top 3 assets with their recommended strategies
            4. Execute crews in parallel (max 3 concurrent)
            5. Wait for all crews to complete
            6. Log aggregated results

        Rate limiting:
            - Handled automatically by thread-safe GeminiConnectionManager
            - Rate limits enforced with blocking logic in get_client method

        Thread safety:
            - Uses ThreadPoolExecutor for safe parallel execution
            - Each crew gets its own instance to avoid state conflicts
        """
        logger.info("Starting new trading cycle.")

        # Step 1: Run market scanner to find opportunities
        logger.info("Running market scanner...")
        scan_results = self.market_scanner.run()
        top_assets = self._parse_scan_results(scan_results)

        if not top_assets:
            logger.warning("Market scanner returned no assets. Ending cycle.")
            return

        # Step 2: Submit trading crews for top assets (up to 3)
        # Add staggered submission to prevent API rate limit spikes
        futures = []
        for asset_config in top_assets[:3]:  # Process top 3 assets
            for strategy in asset_config.get("recommended_strategies", ["3ma"]):
                logger.info(
                    f"Submitting trading crew for {asset_config['symbol']} with strategy {strategy}"
                )
                future = self.executor.submit(
                    self._run_trading_crew,
                    symbol=asset_config["symbol"],
                    strategy=strategy,
                )
                futures.append(future)
                # Add a 2-second delay between crew submissions to stagger API usage
                # This helps prevent all crews from hitting the API simultaneously
                if len(futures) < len(top_assets[:3]) * len(asset_config.get("recommended_strategies", ["3ma"])):
                    time.sleep(2)

        # Step 3: Wait for all submitted crews to complete
        results = [f.result() for f in futures]

        # Step 4: Log summary of all results
        self.log_cycle_summary(results)

    def _parse_scan_results(self, scan_results: Dict) -> List[Dict]:
        """
        Parse and validate market scanner output.

        Args:
            scan_results: Raw output from market scanner crew

        Returns:
            List of asset configurations, each containing:
                - symbol: Stock symbol
                - priority: Priority score (1-5)
                - scores: Dict with volatility, technical, liquidity scores
                - recommended_strategies: List of strategy names
                - reason: Explanation for recommendation

        Returns empty list if parsing fails.
        """
        try:
            return scan_results.get("top_assets", [])
        except Exception as e:
            logger.error(f"Failed to parse market scanner output: {e}")
            logger.debug(f"Raw scanner output:\n{scan_results}")
            return []

    def log_cycle_summary(self, results: List[Dict]):
        """
        Log aggregated results from all trading crews in the cycle.

        Args:
            results: List of execution results from trading crews

        Logs:
            - Success count and details
            - Failure count and error messages
            - Summary statistics
        """
        logger.info("Trading cycle finished. Summary:")
        successes = 0
        failures = 0

        for res in results:
            if res.get("success"):
                successes += 1
                logger.info(
                    f"  - SUCCESS: {res['symbol']} ({res['strategy']}). Result: {res.get('result')}"
                )
            else:
                failures += 1
                logger.error(
                    f"  - FAILED: {res['symbol']} ({res['strategy']}). Error: {res.get('error')}"
                )

        logger.info(
            f"Cycle complete: {successes} succeeded, {failures} failed out of {len(results)} total"
        )


# Global singleton instance for easy access
trading_orchestrator = TradingOrchestrator()
