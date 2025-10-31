#!/usr/bin/env python3
"""
Trading Crew CLI
Advanced command-line interface for Talos Algo AI.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config.settings import settings
from src.crew.trading_crew import trading_crew
from src.crew.market_scanner_crew import MarketScannerCrew
from src.connectors.alpaca_connector import alpaca_manager
from src.utils.logger import setup_logging

console = Console()

@click.group()
def cli():
    """Talos Algo AI - CLI"""
    pass

@cli.command()
@click.option('--strategy', default="3ma", help='Trading strategy to use (default: 3ma)')
@click.option('--symbol', default=None, help='Stock symbol to trade')
@click.option('--timeframe', default='1Min', help='Bar timeframe')
@click.option('--limit', default=100, help='Number of bars')
def run(strategy, symbol, timeframe, limit):
    """Run the trading crew for a single execution with strategy selection."""
    console.print(Panel.fit(
        f"[bold cyan]Talos Algo AI[/bold cyan]\n[dim]Strategy: {strategy}[/dim]",
        border_style="cyan"
    ))
    config_table = Table(show_header=False, box=None)
    config_table.add_column("Parameter", style="cyan")
    config_table.add_column("Value", style="green")
    config_table.add_row("Symbol", symbol or settings.trading_symbol)
    config_table.add_row("Strategy", strategy)
    config_table.add_row("Timeframe", timeframe)
    config_table.add_row("Bars", str(limit))
    config_table.add_row("Mode", "DRY RUN" if settings.dry_run else "LIVE TRADING")
    console.print(config_table)
    if not settings.dry_run:
        console.print("\n[bold red]⚠️  WARNING: LIVE TRADING MODE[/bold red]")
        if not click.confirm("Are you sure you want to execute live trades?"):
            console.print("[yellow]Cancelled by user[/yellow]")
            return
    console.print("\n[cyan]Starting trading crew...[/cyan]\n")
    try:
        result = trading_crew.run(
            symbol=symbol,
            strategy=strategy,
            timeframe=timeframe,
            limit=limit
        )
        if result['success']:
            console.print(Panel.fit(
                "[bold green]✓ Crew execution completed successfully![/bold green]",
                border_style="green"
            ))
            console.print(f"\n[dim]Result: {result['result']}[/dim]")
        else:
            console.print(Panel.fit(
                f"[bold red]✗ Crew execution failed[/bold red]\n"
                f"[dim]{result.get('error', 'Unknown error')}[/dim]",
                border_style="red"
            ))
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]✗ Unexpected error[/bold red]\n"
            f"[dim]{str(e)}[/dim]",
            border_style="red"
        ))

@cli.command()
@click.option('--scan', is_flag=True, help='Run market scanner before trading')
@click.option('--top', default=3, help='Number of top assets to trade')
@click.option('--strategies', default="3ma", help='Comma-separated strategies')
@click.option('--parallel', is_flag=True, help='Run crews in parallel')
@click.option('--symbols', default=None, help='Comma-separated symbols')
def run_multi(scan, top, strategies, parallel, symbols):
    """Run with market scanner, multi-asset, and parallel execution."""
    scanner = MarketScannerCrew()
    assets = []
    if scan:
        scan_results = scanner.run()
        assets = scan_results["top_assets"][:top]
    elif symbols:
        assets = [{"symbol": s.strip(), "recommended_strategies": strategies.split(",")} for s in symbols.split(",")]
    else:
        assets = [{"symbol": settings.trading_symbol, "recommended_strategies": strategies.split(",")}]
    console.print(f"[cyan]Assets to trade:[/cyan] {[a['symbol'] for a in assets]}")
    from concurrent.futures import ThreadPoolExecutor
    results = []
    def run_crew(asset, strategy):
        return trading_crew.run(symbol=asset["symbol"], strategy=strategy)
    with ThreadPoolExecutor(max_workers=top if parallel else 1) as executor:
        futures = []
        for asset in assets:
            for strategy in asset["recommended_strategies"]:
                futures.append(executor.submit(run_crew, asset, strategy))
        for f in futures:
            results.append(f.result())
    console.print(f"[green]Completed {len(results)} crew runs.[/green]")

@cli.command()
@click.option('--auto-scan', is_flag=True, help='Auto-scan market')
@click.option('--interval', default="15m", help='Scan/trade interval')
def interactive(auto_scan, interval):
    """Interactive dashboard (24/7 mode)"""
    from rich.live import Live
    from rich.layout import Layout
    import time
    layout = Layout()
    layout.split_column(
        Layout(name="status", size=3),
        Layout(name="crews"),
        Layout(name="signals"),
        Layout(name="api"),
        Layout(name="portfolio"),
        Layout(name="health"),
        Layout(name="logs", size=8),
        Layout(name="input", size=3)
    )
    with Live(layout, refresh_per_second=1, screen=True):
        for i in range(10):  # Placeholder for demo
            layout["status"].update(Panel("Active Crews: 3"))
            layout["crews"].update(Panel("Crew Status..."))
            layout["signals"].update(Panel("Recent Signals..."))
            layout["api"].update(Panel("API Usage..."))
            layout["portfolio"].update(Panel("Portfolio Summary..."))
            layout["health"].update(Panel("System Health..."))
            layout["logs"].update(Panel("Logs..."))
            layout["input"].update(Panel("Command: [start/stop/pause]"))
            time.sleep(1)

@cli.command()
@click.option('--strategy', default="3ma", help='Strategy to backtest')
@click.option('--symbol', default="SPY", help='Symbol to backtest')
@click.option('--start', required=True, help='Start date (YYYY-MM-DD)')
@click.option('--end', required=True, help='End date (YYYY-MM-DD)')
def backtest(strategy, symbol, start, end):
    """Backtest a strategy on historical data."""
    console.print(f"[cyan]Backtesting {strategy} on {symbol} from {start} to {end}...[/cyan]")
    # Placeholder: implement backtest logic here
    console.print("[green]Backtest complete (stub).[/green]")

@cli.command()
@click.option('--strategies', default="3ma,rsi_breakout,macd", help='Comma-separated strategies')
@click.option('--symbol', default="SPY", help='Symbol to compare')
@click.option('--days', default=30, help='Number of days')
def compare(strategies, symbol, days):
    """Compare strategies on a symbol."""
    strategy_list = strategies.split(",")
    console.print(f"[cyan]Comparing strategies {strategy_list} on {symbol} for {days} days...[/cyan]")
    # Placeholder: implement comparison logic here
    console.print("[green]Comparison complete (stub).[/green]")

@cli.command()
@click.option('--detailed', is_flag=True)
@click.option('--recommendations', is_flag=True)
def status(detailed, recommendations):
    """Show system status with optional recommendations"""
    console.print(Panel.fit(
        "[bold cyan]System Status Check[/bold cyan]",
        border_style="cyan"
    ))
    console.print("\n[cyan]Gemini API Status:[/cyan]")
    try:
        keys = settings.get_gemini_keys_list()
        if keys:
            console.print(f"  ✓ Gemini API keys found in config: [green]{len(keys)} key(s)[/green]")
        else:
            console.print("  [red]✗ Gemini API keys NOT configured in .env[/red]")
    except Exception as e:
        console.print(f"  [red]✗ Error checking Gemini status: {e}[/red]")
    console.print("\n[cyan]Alpaca API Status:[/cyan]")
    try:
        account = alpaca_manager.get_account()
        console.print(f"  ✓ Account Status: {account['status']}")
        console.print(f"  ✓ Equity: ${account['equity']:_}")
        console.print(f"  ✓ Buying Power: ${account['buying_power']:_}")
        console.print(f"  ✓ Mode: {'Paper Trading' if alpaca_manager.is_paper else 'LIVE'}")
    except Exception as e:
        console.print(f"  [red]✗ Error: {e}[/red]")
    console.print("\n[cyan]Current Positions:[/cyan]")
    try:
        positions = alpaca_manager.get_positions()
        if positions:
            for pos in positions:
                console.print(
                    f"  • {pos['symbol']}: {pos['qty']} shares "
                    f"(P&L: ${pos['unrealized_pl']:_})"
                )
        else:
            console.print("  [dim]No open positions[/dim]")
    except Exception as e:
        console.print(f"  [red]✗ Error: {e}[/red]")
    if detailed:
        console.print("\n[cyan]API Health:[/cyan] (stub)")
        console.print("[cyan]Model Performance:[/cyan] (stub)")
        console.print("[cyan]Strategy Win Rates:[/cyan] (stub)")
        console.print("[cyan]Active Positions & P&L:[/cyan] (stub)")
        console.print("[cyan]Rate Limit Utilization:[/cyan] (stub)")
    if recommendations:
        console.print("\n[bold yellow]AI Recommendations:[/bold yellow]")
        console.print("- Consider reducing NVDA position (overbought)")
        console.print("- RSI strategy outperforming 3MA on tech stocks")
        console.print("- Gemini Key #2 showing degraded performance")

@cli.command()
def validate():
    """Run configuration validation checks."""
    import subprocess
    script_path = Path(__file__).parent / "validate_config.py"
    subprocess.run(["python", str(script_path)])

if __name__ == '__main__':
    cli()
