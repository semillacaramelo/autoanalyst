import sys
import time
import logging
from datetime import datetime, timedelta

from rich.console import Console
from rich.live import Live
from rich.table import Table

# Add src to path before local imports
sys.path.insert(0, './src')
from crew.orchestrator import trading_orchestrator
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_status_table(run_count: int, start_time: datetime) -> Table:
    """Generate a table for the live status display."""
    table = Table(title="Talos Algo AI - Live Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    uptime = datetime.now() - start_time
    table.add_row("Status", "Running")
    table.add_row("Uptime", str(uptime).split('.')[0])
    table.add_row("Run Count", str(run_count))
    table.add_row("Parallel Crews", "3")
    table.add_row("Dry Run Mode", str(settings.dry_run))

    return table

def main_loop(run_duration_minutes: int = 120, interval_seconds: int = 300):
    """Main loop to run the trading orchestrator continuously."""
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=run_duration_minutes)
    run_count = 0

    console = Console()
    with Live(generate_status_table(run_count, start_time), console=console, screen=False, refresh_per_second=1) as live:
        while datetime.now() < end_time:
            run_count += 1
            try:
                trading_orchestrator.run_cycle()
            except Exception as e:
                logging.error(f"An error occurred during orchestrator execution: {e}", exc_info=True)

            live.update(generate_status_table(run_count, start_time))

            next_run_time = datetime.now() + timedelta(seconds=interval_seconds)
            while datetime.now() < next_run_time:
                time.sleep(1)
                live.update(generate_status_table(run_count, start_time))

if __name__ == "__main__":
    main_loop()
