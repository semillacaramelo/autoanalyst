#!/usr/bin/env python3
"""
Trading Crew CLI - Command-line interface for the AI-Driven Trading System

This module provides a comprehensive CLI for interacting with the trading system.
It supports multiple execution modes including single crew runs, market scanning,
backtesting, strategy comparison, and autonomous 24/7 trading.

Available Commands:
    run         - Execute trading crew for specific symbol/strategy
    scan        - Run market scanner to find trading opportunities
    status      - Check system status and API connectivity
    backtest    - Run historical backtests on strategies
    compare     - Compare multiple strategies side-by-side
    autonomous  - Launch 24/7 autonomous trading mode
    interactive - Display real-time monitoring dashboard
    validate    - Validate configuration and API connectivity

Usage:
    python scripts/run_crew.py [COMMAND] [OPTIONS]
    python scripts/run_crew.py --help
    python scripts/run_crew.py [COMMAND] --help

Examples:
    # Check system status
    python scripts/run_crew.py status
    
    # Run trading crew for SPY with 3MA strategy
    python scripts/run_crew.py run --symbol SPY --strategy 3ma
    
    # Backtest a strategy
    python scripts/run_crew.py backtest --symbol AAPL --strategy rsi_breakout
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
    """
    Run the trading crew with various execution modes.
    
    This command supports multiple execution modes:
    1. Single symbol/strategy execution (default)
    2. Multiple symbols/strategies sequentially or in parallel
    3. Market scanner mode to automatically select top opportunities
    
    The crew follows a 4-agent workflow:
    - Data Collection: Fetch and validate market data
    - Signal Generation: Apply trading strategy to generate signals
    - Risk Management: Enforce position sizing and portfolio constraints
    - Execution: Place approved trades via Alpaca API
    
    Examples:
        # Run for single symbol with default strategy (3ma)
        python scripts/run_crew.py run --symbols AAPL
        
        # Run multiple strategies on one symbol
        python scripts/run_crew.py run --symbols SPY --strategies 3ma,rsi_breakout
        
        # Run with market scanner
        python scripts/run_crew.py run --scan --top 5
        
        # Parallel execution
        python scripts/run_crew.py run --symbols SPY,QQQ --strategies 3ma,macd --parallel
    """
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
    """
    Helper function to run a single trading crew and print results.
    
    Args:
        symbol: Stock symbol to trade
        strategy: Trading strategy name
        timeframe: Bar timeframe (e.g., '1Min', '5Min', '1Day')
        limit: Number of historical bars to fetch
        
    Displays:
        - Configuration summary
        - Live trading warning (if applicable)
        - Execution results or error messages
    """
    # Display configuration
    config_table = Table(show_header=False, box=None)
    config_table.add_column("Parameter", style="cyan")
    config_table.add_column("Value", style="green")
    config_table.add_row("Symbol", symbol)
    config_table.add_row("Strategy", strategy)
    config_table.add_row("Timeframe", timeframe)
    config_table.add_row("Bars", str(limit))
    config_table.add_row("Mode", "DRY RUN" if settings.dry_run else "LIVE TRADING")
    console.print(config_table)

    # Safety check for live trading
    if not settings.dry_run:
        console.print("\n[bold red]⚠️  WARNING: LIVE TRADING MODE[/bold red]")
        console.print("[yellow]Real trades will be placed with real money![/yellow]")
        if not click.confirm("Are you sure you want to execute live trades?"):
            console.print("[yellow]Cancelled by user[/yellow]")
            return

    try:
        # Execute the trading crew
        result = trading_crew.run(symbol=symbol, strategy=strategy, timeframe=timeframe, limit=limit)
        
        if result['success']:
            console.print(Panel.fit("[bold green]✓ Crew execution completed successfully![/bold green]", border_style="green"))
            console.print(f"\n[dim]Result: {result['result']}[/dim]")
        else:
            console.print(Panel.fit(f"[bold red]✗ Crew execution failed[/bold red]\n[dim]{result.get('error', 'Unknown error')}[/dim]", border_style="red"))
            
            # Provide helpful suggestions based on error type
            error_msg = str(result.get('error', '')).lower()
            if 'connection' in error_msg or 'network' in error_msg:
                console.print("\n[yellow]Suggestion:[/yellow] Check your internet connection and API credentials")
            elif 'rate limit' in error_msg:
                console.print("\n[yellow]Suggestion:[/yellow] You've hit API rate limits. Wait a few minutes and try again")
            elif 'invalid' in error_msg and 'symbol' in error_msg:
                console.print("\n[yellow]Suggestion:[/yellow] Verify the stock symbol is valid and traded on US exchanges")
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Execution interrupted by user[/yellow]")
    except Exception as e:
        console.print(Panel.fit(f"[bold red]✗ Unexpected error[/bold red]\n[dim]{str(e)}[/dim]", border_style="red"))
        console.print("\n[yellow]Suggestion:[/yellow] Check logs/trading_crew_*.log for detailed error information")


@cli.command()
def scan():
    """
    Run the market scanner crew to find trading opportunities.
    
    The market scanner analyzes the S&P 100 constituents across multiple dimensions:
    - Volatility analysis: Identifies stocks with optimal volatility
    - Technical setup: Analyzes technical indicators and patterns
    - Liquidity filter: Ensures adequate daily trading volume (>1M shares)
    - Chief analyst: Synthesizes results and recommends top opportunities
    
    Output: JSON with top 5 assets ranked by priority, including:
    - Symbol and priority score
    - Individual scores (volatility, technical, liquidity)
    - Recommended trading strategies
    - Reasoning for the recommendation
    
    Note: This command can take several minutes to complete as it analyzes
    100+ stocks with multiple AI agents.
    
    Example:
        python scripts/run_crew.py scan
    """
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
    """
    Check system status and connectivity.
    
    Displays current status of all system components:
    - Alpaca API: Account status, equity, trading mode, data feed
    - Gemini API: Number of API keys configured
    - Rate Limiter: Current API usage vs budgets (with --detailed)
    - API Key Health: Success/failure tracking for each key (with --detailed)
    
    Options:
        --detailed: Show comprehensive status including API key health tracking
                   and rate limiter utilization
        --recommendations: Generate AI-powered recommendations based on system status
    
    Examples:
        # Basic status check
        python scripts/run_crew.py status
        
        # Detailed status with key health
        python scripts/run_crew.py status --detailed
        
        # Get AI recommendations
        python scripts/run_crew.py status --recommendations
    """
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
    if detailed and trading_orchestrator.global_rate_limiter:
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
    elif detailed and not trading_orchestrator.global_rate_limiter:
        console.print("\n[yellow]Rate Limiter: Not yet implemented[/yellow]")

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
    """
    Run a historical backtest for a single strategy.
    
    Simulates the strategy's performance over a historical period using
    actual market data. The backtest engine replays historical bars and
    executes trades according to the strategy's rules.
    
    Metrics calculated:
    - Total trades executed
    - Total P&L (profit/loss)
    - Win rate (percentage of profitable trades)
    - Sharpe ratio (risk-adjusted returns)
    - Sortino ratio (downside risk-adjusted returns)
    - Calmar ratio (return vs max drawdown)
    - Maximum drawdown
    
    Available strategies:
    - 3ma: Triple moving average crossover
    - rsi_breakout: RSI-based breakout strategy
    - macd: MACD crossover strategy
    - bollinger_bands_reversal: Bollinger Bands mean reversion
    
    Examples:
        # Backtest 3MA on SPY for 6 months
        python scripts/run_crew.py backtest --symbol SPY --strategy 3ma
        
        # Backtest RSI breakout on AAPL for full year
        python scripts/run_crew.py backtest --symbol AAPL --strategy rsi_breakout --start 2024-01-01 --end 2024-12-31
    """
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
    """
    Compare the performance of multiple strategies.
    
    Runs backtests for multiple strategies on the same asset and time period,
    then presents a side-by-side comparison of their performance metrics.
    This helps identify which strategy performs best for a given asset.
    
    Output includes for each strategy:
    - All standard backtest metrics (trades, P&L, win rate, ratios, drawdown)
    - Relative performance comparison
    - Best strategy recommendation
    
    Examples:
        # Compare 3MA and RSI strategies on SPY
        python scripts/run_crew.py compare --symbol SPY --strategies 3ma,rsi_breakout
        
        # Compare all strategies on NVDA
        python scripts/run_crew.py compare --symbol NVDA --strategies 3ma,rsi_breakout,macd,bollinger_bands_reversal
        
        # Full year comparison
        python scripts/run_crew.py compare --symbol QQQ --strategies 3ma,macd --start 2024-01-01 --end 2024-12-31
    """
    console.print(Panel.fit(f"[bold cyan]Comparing Strategies on {symbol}[/bold cyan]", border_style="cyan"))
    backtester = BacktesterV2(start_date=start, end_date=end)
    strategy_list = strategies.split(',')
    results = backtester.compare(symbol, strategy_list)
    console.print(json.dumps(results, indent=2))

@cli.command()
def autonomous():
    """
    Launch the system in 24/7 autonomous trading mode.
    
    In autonomous mode, the system:
    - Continuously monitors the market according to market calendar
    - Automatically runs market scans during trading hours
    - Executes trades based on crew recommendations
    - Manages open positions and risk limits
    - Automatically pauses during market closures
    - Respects daily trade limits and loss limits
    
    The scheduler follows the US market calendar:
    - Active: Monday-Friday, 9:30 AM - 4:00 PM ET
    - Closed: Weekends and US market holidays
    
    Safety features:
    - DRY_RUN mode by default (set in .env)
    - Daily loss limits enforced
    - Maximum position limits enforced
    - Automatic error recovery with circuit breakers
    
    To enable:
        1. Set AUTONOMOUS_MODE_ENABLED=true in .env
        2. Configure MAX_DAILY_TRADES and other limits
        3. Test thoroughly in DRY_RUN mode first
        4. Set DRY_RUN=false only when ready for live trading
    
    Example:
        python scripts/run_crew.py autonomous
        
    Press Ctrl+C to stop autonomous mode.
    """
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
        equity = account.get('equity')
        if equity is None:
            equity_str = "N/A"
        else:
            equity_str = f"${float(equity):,.2f}"
        alpaca_status = f"[green]Connected[/green] (Equity: {equity_str})"
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
    """
    Launch the interactive dashboard for real-time monitoring.
    
    Provides a live, terminal-based dashboard with:
    - System status (Alpaca and Gemini API connectivity)
    - Current account equity and trading mode
    - Open positions with real-time P&L
    - Recent log messages
    - Auto-refresh every 5 seconds
    
    The dashboard uses Rich library for terminal graphics and updates
    automatically without requiring user input.
    
    Navigation:
    - Dashboard auto-refreshes every 5 seconds
    - Press Ctrl+C to exit
    
    Requirements:
    - Terminal with ANSI color support
    - Minimum terminal size: 80x24 characters
    
    Example:
        python scripts/run_crew.py interactive
    """
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
    """
    Run configuration validation checks.
    
    Validates all system configuration before running trading operations:
    
    1. Gemini API Keys:
       - Checks that keys are properly formatted
       - Verifies keys are loaded from environment
       - Shows masked key values for security
    
    2. Alpaca Connection:
       - Validates API credentials format
       - Confirms base URL configuration
       - Verifies data feed setting (IEX vs SIP)
    
    3. Strategy Parameters:
       - Validates trading symbol
       - Checks moving average periods (fast < medium < slow)
       - Verifies volume and ADX thresholds
    
    4. Risk Management:
       - Validates max risk per trade (0-100%)
       - Checks max open positions limit
       - Verifies daily loss limit setting
    
    Exit codes:
        0: All checks passed
        1: One or more checks failed
    
    Note: Live API connectivity tests are skipped if network is unavailable.
    
    Example:
        python scripts/run_crew.py validate
    """
    import subprocess
    script_path = Path(__file__).parent / "validate_config.py"
    subprocess.run(["python", str(script_path)])


if __name__ == '__main__':
    cli()
