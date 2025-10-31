import sys
import time
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from collections import deque

from rich.console import Console
from rich.live import Live
from rich.table import Table

# Add src to path before local imports
sys.path.insert(0, './src')
from crew.market_scanner_crew import MarketScannerCrew
from crew.trading_crew import trading_crew
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GlobalRateLimiter:
    """Coordinates API usage across all parallel crews"""
    def __init__(self):
        self.gemini_rpm_budget = settings.rate_limit_rpm * 0.8
        self.gemini_rpd_budget = settings.rate_limit_rpd * 0.8
        self.alpaca_rpm_budget = 180
        self.gemini_rpm_used = deque()
        self.gemini_rpd_used = deque()
        self.alpaca_rpm_used = deque()

    def can_start_crew(self) -> bool:
        projected_gemini = len(self.gemini_rpm_used) + 14
        projected_alpaca = len(self.alpaca_rpm_used) + 10
        return (projected_gemini < self.gemini_rpm_budget and 
                projected_alpaca < self.alpaca_rpm_budget)

    def register_api_call(self, service: str):
        now = time.time()
        if service == "gemini":
            self.gemini_rpm_used.append(now)
            self.gemini_rpd_used.append(now)
        elif service == "alpaca":
            self.alpaca_rpm_used.append(now)
        # Clean up old entries
        while self.gemini_rpm_used and now - self.gemini_rpm_used[0] > 60:
            self.gemini_rpm_used.popleft()
        while self.gemini_rpd_used and now - self.gemini_rpd_used[0] > 86400:
            self.gemini_rpd_used.popleft()
        while self.alpaca_rpm_used and now - self.alpaca_rpm_used[0] > 60:
            self.alpaca_rpm_used.popleft()

class TradingOrchestrator:
    def __init__(self):
        self.market_scanner = MarketScannerCrew()
        self.active_crews = {}
        self.global_rate_limiter = GlobalRateLimiter()
        self.executor = ThreadPoolExecutor(max_workers=3)

    def run_cycle(self):
        scan_results = self.market_scanner.run()
        futures = []
        for asset_config in scan_results["top_assets"][:3]:
            for strategy in asset_config["recommended_strategies"]:
                if self.global_rate_limiter.can_start_crew():
                    future = self.executor.submit(
                        self.run_trading_crew,
                        symbol=asset_config["symbol"],
                        strategy=strategy
                    )
                    futures.append(future)
        results = [f.result() for f in futures]
        self.log_cycle_summary(results)

    def run_trading_crew(self, symbol: str, strategy: str, timeframe: str = "1Min", limit: int = 100):
        # This should instantiate and run a TradingCrew with the given params
        # For now, use the existing trading_crew as a placeholder
        inputs = {"symbol": symbol, "strategy": strategy, "timeframe": timeframe, "limit": limit}
        result = trading_crew.run(inputs)
        return {"symbol": symbol, "strategy": strategy, "result": result}

    def log_cycle_summary(self, results):
        logging.info("Cycle Summary:")
        for r in results:
            logging.info(f"Asset: {r['symbol']} | Strategy: {r['strategy']} | Result: {r['result']}")

def generate_status_table(run_count: int, last_result: dict, start_time: datetime) -> Table:
    table = Table(title="Talos Algo AI - Live Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    uptime = datetime.now() - start_time
    table.add_row("Status", "Running")
    table.add_row("Uptime", str(uptime).split('.')[0])
    table.add_row("Run Count", str(run_count))
    table.add_row("Dry Run Mode", str(settings.dry_run))
    if last_result:
        table.add_row("Last Run Status", "Success" if not last_result.get("error") else "Failed")
        table.add_row("Last Final Answer", str(last_result.get("final_answer", "N/A")))
    return table

def main_loop(run_duration_minutes: int = 60, interval_seconds: int = 60):
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=run_duration_minutes)
    run_count = 0
    last_result = {}
    orchestrator = TradingOrchestrator()
    console = Console()
    with Live(generate_status_table(run_count, last_result, start_time), console=console, screen=False, refresh_per_second=1) as live:
        while datetime.now() < end_time:
            run_count += 1
            try:
                orchestrator.run_cycle()
                last_result = {"final_answer": "Cycle completed", "error": None}
            except Exception as e:
                logging.error(f"An error occurred during orchestrator execution: {e}")
                last_result = {"final_answer": None, "error": str(e)}
            live.update(generate_status_table(run_count, last_result, start_time))
            next_run_time = datetime.now() + timedelta(seconds=interval_seconds)
            while datetime.now() < next_run_time:
                time.sleep(1)
                live.update(generate_status_table(run_count, last_result, start_time))

if __name__ == "__main__":
    main_loop(run_duration_minutes=60, interval_seconds=60)
