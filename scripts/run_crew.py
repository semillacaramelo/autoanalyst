#!/usr/bin/env python3
"""
Trading Crew CLI
Command-line interface for running the trading crew and market scanner.
"""
import click
import json
import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.live import Live
from rich.layout import Layout
from pathlib import Path
import sys

# Add src to path before other project imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.crew.trading_crew import trading_crew
from src.crew.market_scanner_crew import market_scanner_crew
from src.crew.orchestrator import trading_orchestrator
from src.connectors.alpaca_connector import alpaca_manager
from src.connectors.gemini_connector import gemini_manager
from src.utils.backtester_v2 import BacktesterV2
from src.utils.global_scheduler import AutoTradingScheduler
from src.utils.logger import setup_logging

console = Console()


@click.group()
def cli():
    """AI-Driven Trading Crew - Backend CLI"""
    pass


@cli.command()
@click.option('--symbols', default=None, help='Comma-separated stock symbols to trade')
@click.option('--strategies', default='3ma', help='Comma-separated strategies to use')
@click.option('--parallel', is_flag=True, help='Run crews in parallel for multiple symbols/strategies')
@click.option('--scan', is_flag=True, help='Run market scanner to find symbols and strategies')
@click.option('--top', default=3, help='Number of top assets to select from scanner results')
@click.option('--timeframe', default='1Min', help='Bar timeframe (1Min, 5Min, etc.)')
@click.option('--limit', default=100, help='Number of historical bars to fetch')
def run(symbols, strategies, parallel, scan, top, timeframe, limit):
    """Run the trading crew with various execution modes."""
    console.print(Panel.fit(
        "[bold cyan]AI-Driven Trading Crew[/bold cyan]\n"
        "[dim]Backend-First Development Version[/dim]",
        border_style="cyan"
    ))

    if scan:
        console.print("\n[cyan]Running in Market Scanner mode...[/cyan]")
        trading_orchestrator.run_cycle()
        return

    symbol_list = symbols.split(',') if symbols else [settings.trading_symbol]
    strategy_list = strategies.split(',')

    if len(symbol_list) > 1 or len(strategy_list) > 1:
        if parallel:
            console.print("\n[cyan]Running in Parallel Multi-Crew mode...[/cyan]")
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for symbol in symbol_list:
                    for strategy in strategy_list:
                        console.print(f"  - Submitting job for {symbol} with strategy {strategy}")
                        futures.append(executor.submit(trading_crew.run, symbol=symbol, strategy=strategy, timeframe=timeframe, limit=limit))

                for future in futures:
                    result = future.result()
                    if result['success']:
                        console.print(f"[green]  ✓ SUCCESS: {result['symbol']} ({result['strategy']})[/green]")
                    else:
                        console.print(f"[red]  ✗ FAILED: {result['symbol']} ({result['strategy']}) - {result['error']}[/red]")
        else: # Sequential multi-run
            console.print("\n[cyan]Running in Sequential Multi-Crew mode...[/cyan]")
            for symbol in symbol_list:
                for strategy in strategy_list:
                    console.print(f"\n[yellow]Executing for {symbol} with strategy {strategy}...[/yellow]")
                    run_single_crew(symbol, strategy, timeframe, limit)
    else: # Single run
        console.print("\n[cyan]Running in Single Crew mode...[/cyan]")
        run_single_crew(symbol_list[0], strategy_list[0], timeframe, limit)


def run_single_crew(symbol, strategy, timeframe, limit):
    """Helper function to run a single trading crew and print results."""
    config_table = Table(show_header=False, box=None)
    config_table.add_column("Parameter", style="cyan")
    config_table.add_column("Value", style="green")
    config_table.add_row("Symbol", symbol)
    config_table.add_row("Strategy", strategy)
    config_table.add_row("Mode", "DRY RUN" if settings.dry_run else "LIVE TRADING")
    console.print(config_table)

    if not settings.dry_run:
        console.print("\n[bold red]⚠️  WARNING: LIVE TRADING MODE[/bold red]")
        if not click.confirm("Are you sure you want to execute live trades?"):
            console.print("[yellow]Cancelled by user[/yellow]")
            return

    try:
        result = trading_crew.run(symbol=symbol, strategy=strategy, timeframe=timeframe, limit=limit)
        if result['success']:
            console.print(Panel.fit("[bold green]✓ Crew execution completed successfully![/bold green]", border_style="green"))
            console.print(f"\n[dim]Result: {result['result']}[/dim]")
        else:
            console.print(Panel.fit(f"[bold red]✗ Crew execution failed[/bold red]\n[dim]{result.get('error', 'Unknown error')}[/dim]", border_style="red"))
    except Exception as e:
        console.print(Panel.fit(f"[bold red]✗ Unexpected error[/bold red]\n[dim]{str(e)}[/dim]", border_style="red"))


@cli.command()
def scan():
    """Run the market scanner crew to find opportunities."""
    console.print(Panel.fit(
        "[bold cyan]Market Scanner Crew[/bold cyan]",
        border_style="cyan"
    ))
    console.print("\n[cyan]Scanning the S&P 100 for trading opportunities...[/cyan]\n")

    try:
        raw_result = market_scanner_crew.run()
        json_string = raw_result.strip().removeprefix("```json").removesuffix("```")
        scan_data = json.loads(json_string)

        console.print(Panel.fit("[bold green]✓ Market scan completed successfully![/bold green]", border_style="green"))
        console.print("\n[yellow]Scan Results:[/yellow]")
        syntax = Syntax(json.dumps(scan_data, indent=2), "json", theme="solarized-dark", line_numbers=True)
        console.print(syntax)

    except json.JSONDecodeError:
        console.print(Panel.fit("[bold red]✗ Failed to parse scanner output[/bold red]", border_style="red"))
        console.print("\n[yellow]Raw Output:[/yellow]")
        console.print(raw_result)
    except Exception as e:
        console.print(Panel.fit(f"[bold red]✗ Unexpected error during scan[/bold red]\n[dim]{str(e)}[/dim]", border_style="red"))

@cli.command()
@click.option('--detailed', is_flag=True, help='Show detailed status including API key health.')
@click.option('--recommendations', is_flag=True, help='Generate AI-powered recommendations.')
def status(detailed, recommendations):
    """Check system status and connectivity."""
    console.print(Panel.fit("[bold cyan]System Status Check[/bold cyan]", border_style="cyan"))

    # Alpaca Status
    console.print("\n[cyan]Alpaca API Status:[/cyan]")
    try:
        account = alpaca_manager.get_account()
        console.print(f"  ✓ Account Status: {account['status']}")
        console.print(f"  ✓ Equity: ${account['equity']:_}")
        console.print(f"  ✓ Mode: {'Paper Trading' if alpaca_manager.is_paper else 'LIVE'}")
        console.print(f"  ✓ Data Feed: [bold yellow]{settings.alpaca_data_feed.upper()}[/bold yellow]")
    except Exception as e:
        console.print(f"  [red]✗ Error: {e}[/red]")

    # Gemini Status
    console.print("\n[cyan]Gemini API Status:[/cyan]")
    keys = settings.get_gemini_keys_list()
    console.print(f"  ✓ API keys found: [green]{len(keys)}[/green]")
    if detailed:
        health_table = Table(title="Gemini API Key Health")
        health_table.add_column("Key (last 4)", style="cyan")
        health_table.add_column("Success", style="green")
        health_table.add_column("Failure", style="red")
        health_table.add_column("Health Score", style="yellow")
        for key, stats in gemini_manager.key_health_tracker.key_health.items():
            score = gemini_manager.key_health_tracker._calculate_health_score(key)
            health_table.add_row(f"...{key[-4:]}", str(stats['success']), str(stats['failure']), f"{score:.0%}")
        console.print(health_table)

    # Rate Limiter Status
    if detailed:
        console.print("\n[cyan]Rate Limiter Status (Last Minute):[/cyan]")
        rate_table = Table(title="API Rate Limit Utilization")
        rate_table.add_column("Service", style="cyan")
        rate_table.add_column("Usage", style="magenta")
        rate_table.add_column("Budget", style="green")
        limiter = trading_orchestrator.global_rate_limiter
        limiter._cleanup() # Ensure deque is up-to-date
        rate_table.add_row("Gemini", f"{len(limiter.gemini_rpm_used)} RPM", f"{limiter.gemini_rpm_budget:.0f} RPM")
        rate_table.add_row("Alpaca", f"{len(limiter.alpaca_rpm_used)} RPM", f"{limiter.alpaca_rpm_budget:.0f} RPM")
        console.print(rate_table)

    # Recommendations
    if recommendations:
        console.print("\n[cyan]Generating AI Recommendations...[/cyan]")
        try:
            from crewai import Agent, Task, Crew
            from crewai.llm import LLM

            llm = LLM(model=f"gemini/{settings.primary_llm_models[0]}")

            status_summary = f"Alpaca Account: {account}, Gemini Key Health: {gemini_manager.key_health_tracker.key_health}"

            recommender = Agent(role="AI System Health Analyst", goal="Analyze system status and provide recommendations.", backstory="An expert AI.", llm=llm, verbose=False)
            rec_task = Task(description=f"Analyze: {status_summary}", expected_output="Recommendations.", agent=recommender)

            recommendation_crew = Crew(agents=[recommender], tasks=[rec_task], verbose=False)
            recommendation_text = str(recommendation_crew.kickoff())
            console.print(Panel(recommendation_text, title="[yellow]Recommendations[/yellow]", border_style="yellow"))
        except Exception as e:
            console.print(f"  [red]✗ Failed to generate recommendations: {e}[/red]")

@cli.command()
@click.option('--strategy', default='3ma', help='Strategy to backtest.')
@click.option('--symbol', default='SPY', help='Symbol to backtest on.')
@click.option('--start', default='2024-01-01', help='Start date (YYYY-MM-DD).')
@click.option('--end', default='2024-06-30', help='End date (YYYY-MM-DD).')
def backtest(strategy, symbol, start, end):
    """Run a historical backtest for a single strategy."""
    console.print(Panel.fit(f"[bold cyan]Backtesting {strategy} on {symbol}[/bold cyan]", border_style="cyan"))
    backtester = BacktesterV2(start_date=start, end_date=end)
    results = backtester.run(symbol, strategy)
    console.print(json.dumps(results, indent=2))

@cli.command()
@click.option('--strategies', default='3ma,rsi_breakout', help='Comma-separated strategies to compare.')
@click.option('--symbol', default='SPY', help='Symbol to compare on.')
@click.option('--start', default='2024-01-01', help='Start date (YYYY-MM-DD).')
@click.option('--end', default='2024-06-30', help='End date (YYYY-MM-DD).')
def compare(strategies, symbol, start, end):
    """Compare the performance of multiple strategies."""
    console.print(Panel.fit(f"[bold cyan]Comparing Strategies on {symbol}[/bold cyan]", border_style="cyan"))
    backtester = BacktesterV2(start_date=start, end_date=end)
    strategy_list = strategies.split(',')
    results = backtester.compare(symbol, strategy_list)
    console.print(json.dumps(results, indent=2))

@cli.command()
def autonomous():
    """Launch the system in 24/7 autonomous trading mode."""
    console.print(Panel.fit("[bold cyan]Entering 24/7 Autonomous Trading Mode[/bold cyan]", border_style="cyan"))
    if not settings.autonomous_mode_enabled:
        console.print("[yellow]Warning: Autonomous mode is not enabled in settings. Running for one cycle.[/yellow]")

    scheduler = AutoTradingScheduler()
    scheduler.run_forever()

def get_status_panel() -> Panel:
    """Returns a Panel with the current system status."""
    table = Table(show_header=False, box=None)
    table.add_column("key", style="cyan")
    table.add_column("value")

    try:
        account = alpaca_manager.get_account()
        alpaca_status = f"[green]Connected[/green] (Equity: ${account.get('equity'):,.2f})"
    except Exception:
        alpaca_status = "[red]Connection Failed[/red]"

    try:
        gemini_keys = settings.get_gemini_keys_list()
        gemini_manager.get_client() # Tries to get a healthy client
        gemini_status = f"[green]Connected[/green] ({len(gemini_keys)} keys)"
    except Exception:
        gemini_status = "[red]Connection Failed[/red]"

    trading_mode = "[bold yellow]DRY RUN[/bold yellow]" if settings.dry_run else "[bold red]LIVE TRADING[/bold red]"

    table.add_row("Alpaca API:", alpaca_status)
    table.add_row("Gemini API:", gemini_status)
    table.add_row("Trading Mode:", trading_mode)

    return Panel(table, title="System Status", border_style="green")


def get_positions_panel() -> Panel:
    """Returns a Panel with current open positions."""
    try:
        positions = alpaca_manager.get_positions()
        if not positions:
            return Panel("[dim]No open positions[/dim]", title="Open Positions", border_style="yellow")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Symbol", style="cyan")
        table.add_column("Qty", justify="right")
        table.add_column("P&L", justify="right")

        for pos in positions:
            pl = pos.get('unrealized_pl', 0.0)
            pl_str = f"[green]${pl:,.2f}[/green]" if pl >= 0 else f"[red]${pl:,.2f}[/red]"
            table.add_row(pos['symbol'], str(pos['qty']), pl_str)

        return Panel(table, title="Open Positions", border_style="yellow")
    except Exception as e:
        return Panel(f"[red]Error fetching positions: {e}[/red]", title="Open Positions", border_style="red")


def generate_dashboard() -> Layout:
    """Creates the layout for the interactive dashboard."""
    layout = Layout(name="root")

    layout.split(
        Layout(name="header", size=3),
        Layout(ratio=1, name="main"),
        Layout(size=10, name="footer"),
    )

    layout["main"].split_row(Layout(name="side"), Layout(name="body", ratio=2))
    layout["side"].split(Layout(name="status"), Layout(name="positions"))
    layout["footer"].update(Panel("[dim]Logs will be displayed here in a future enhancement...[/dim]", title="Logs", border_style="blue"))
    return layout


@cli.command()
def interactive():
    """Launch the interactive dashboard for real-time monitoring."""
    layout = generate_dashboard()

    layout["header"].update(
        Panel(f"[bold green]Talos Algo AI - Interactive Dashboard[/bold green]\nLast updated: {datetime.now().ctime()}", border_style="cyan")
    )
    layout["body"].update(Panel("Welcome! System data will refresh every 5 seconds. Press Ctrl+C to exit.", title="Activity", border_style="blue"))

    with Live(layout, screen=True, redirect_stderr=False, refresh_per_second=4) as live:
        try:
            while True:
                time.sleep(5)
                layout["header"].update(
                    Panel(f"[bold green]Talos Algo AI - Interactive Dashboard[/bold green]\nLast updated: {datetime.now().ctime()}", border_style="cyan")
                )
                layout["status"].update(get_status_panel())
                layout["positions"].update(get_positions_panel())
        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard stopped by user. Exiting.[/yellow]")


@cli.command()
def validate():
    """Run configuration validation checks."""
    import subprocess
    script_path = Path(__file__).parent / "validate_config.py"
    subprocess.run(["python", str(script_path)])


if __name__ == '__main__':
    cli()
