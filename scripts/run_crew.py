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
from src.utils.state_manager import StateManager
import pytz

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

    # Use provided symbols or fallback to TRADING_SYMBOL from .env (only for manual testing)
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
    config_table.add_row("Mode", "DRY RUN" if settings.dry_run else "PAPER TRADING")
    console.print(config_table)

    # Note: No confirmation needed for paper trading - it uses simulated money
    if not settings.dry_run:
        console.print("\n[bold green]📊 PAPER TRADING MODE[/bold green]")
        console.print("[cyan]Trades will be executed with Alpaca paper account (simulated funds)[/cyan]")

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
    Run the intelligent market scanner to find trading opportunities.
    
    The market scanner automatically:
    - Detects the best active market (US Equity during market hours, Crypto 24/7)
    - Analyzes market-appropriate assets (S&P 100, crypto pairs, or forex)
    - Uses 4 AI agents to evaluate opportunities:
      * Volatility Analyzer: Identifies optimal price movement
      * Technical Analyst: Evaluates indicators and patterns
      * Liquidity Filter: Ensures tradeable volume
      * Chief Analyst: Synthesizes and ranks top 5 opportunities
    
    Output: Top 5 assets with:
    - Priority ranking
    - Performance scores (volatility, technical, liquidity)
    - Recommended strategies for each asset
    - AI reasoning for recommendations
    
    Market Selection:
    - US Equity hours (9:30am-4pm ET): Scans S&P 100 stocks
    - After hours / weekends: Scans cryptocurrency pairs
    - Auto-detects best market based on current time
    
    Note: Scanning takes 1-3 minutes depending on market size.
    
    Example:
        python scripts/run_crew.py scan
    """
    console.print(Panel.fit(
        "[bold cyan]🔍 Intelligent Market Scanner[/bold cyan]\\n"
        "[dim]Auto-detecting optimal market and opportunities...[/dim]",
        border_style="cyan"
    ))
    
    # Show which market will be scanned
    from src.utils.market_calendar import MarketCalendar
    market_calendar = MarketCalendar()
    active_markets = market_calendar.get_active_markets(
        datetime.now(pytz.utc), ['US_EQUITY', 'CRYPTO']
    )
    
    if 'US_EQUITY' in active_markets:
        scan_market = 'US_EQUITY'
        asset_type = 'S&P 100 stocks'
    else:
        scan_market = 'CRYPTO'
        asset_type = 'cryptocurrency pairs'
    
    console.print(f"\\n[cyan]→ Selected Market:[/cyan] [bold]{scan_market}[/bold]")
    console.print(f"[cyan]→ Analyzing:[/cyan] {asset_type}")
    console.print(f"[cyan]→ Agents:[/cyan] 4 AI agents (Volatility, Technical, Liquidity, Chief)\\n")

    try:
        console.print("[yellow]⚙️  Running scanner... (this may take 1-3 minutes)[/yellow]\\n")
        raw_result = market_scanner_crew.run()
        json_string = raw_result.strip().removeprefix("```json").removesuffix("```")
        scan_data = json.loads(json_string)

        console.print(Panel.fit("[bold green]✓ Market scan completed![/bold green]", border_style="green"))
        console.print("\\n[bold]📊 Top Trading Opportunities:[/bold]\\n")
        
        # Pretty print the results
        syntax = Syntax(json.dumps(scan_data, indent=2), "json", theme="monokai", line_numbers=False)
        console.print(syntax)
        
        # Show quick summary
        if 'top_assets' in scan_data and scan_data['top_assets']:
            console.print("\\n[bold cyan]Quick Summary:[/bold cyan]")
            for i, asset in enumerate(scan_data['top_assets'][:3], 1):
                symbol = asset.get('symbol', 'N/A')
                strategies = ', '.join(asset.get('recommended_strategies', []))
                console.print(f"  {i}. [bold]{symbol}[/bold] - Strategies: {strategies}")

    except json.JSONDecodeError:
        console.print(Panel.fit("[bold red]✗ Failed to parse scanner output[/bold red]", border_style="red"))
        console.print("\\n[yellow]Raw Output:[/yellow]")
        console.print(raw_result)
    except Exception as e:
        console.print(Panel.fit(f"[bold red]✗ Unexpected error during scan[/bold red]\\n[dim]{str(e)}[/dim]", border_style="red"))
        console.print("\\n[yellow]Tip:[/yellow] Check that the market is open or try again in a few moments.")

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

def _generate_autonomous_status_table(run_count: int, start_time: datetime, scheduler) -> Table:
    """Generate live status table for autonomous mode with UI (migrated from main.py)."""
    table = Table(title="AutoAnalyst - Autonomous Trading Status", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan", width=30)
    table.add_column("Value", style="magenta")

    uptime = datetime.now() - start_time
    uptime_str = str(uptime).split('.')[0]  # Remove microseconds
    
    # Get current market from rotation state if available
    try:
        from utils.state_manager import StateManager
        state_manager = StateManager()
        rotation_state = state_manager.load_state('market_rotation_state.json')
        current_market = rotation_state.get('current_market', 'Unknown')
    except:
        current_market = 'Unknown'
    
    table.add_row("🟢 Status", "Running")
    table.add_row("⏱️  Uptime", uptime_str)
    table.add_row("🔄 Cycle Count", str(run_count))
    table.add_row("🌍 Current Market", current_market)
    table.add_row("💰 Mode", "DRY RUN" if settings.dry_run else "PAPER TRADING")
    table.add_row("📊 Max Positions", str(settings.max_open_positions))
    table.add_row("🎯 Risk Per Trade", f"{settings.max_risk_per_trade * 100}%")
    table.add_row("🛑 Daily Loss Limit", f"{settings.daily_loss_limit * 100}%")

    return table

def _autonomous_with_ui():
    """Run autonomous mode with live status UI (migrated from main.py)."""
    from datetime import datetime
    import time
    from rich.live import Live
    import threading
    
    start_time = datetime.now()
    run_count = [0]  # Use list to allow modification in nested function
    scheduler = AutoTradingScheduler()
    stop_event = threading.Event()
    
    console.print(Panel.fit(
        "[bold cyan]🤖 Autonomous Mode with Live UI[/bold cyan]\\n\\n"
        "[green]✓[/green] Real-time status display\\n"
        "[green]✓[/green] 24/7 continuous operation\\n"
        "[green]✓[/green] Press Ctrl+C to stop gracefully\\n\\n"
        f"[dim]Started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
        border_style="cyan"
    ))
    
    def run_scheduler():
        """Run scheduler in separate thread and track cycles."""
        original_run_cycle = scheduler.orchestrator.run_cycle
        
        def wrapped_run_cycle(*args, **kwargs):
            result = original_run_cycle(*args, **kwargs)
            run_count[0] += 1
            return result
        
        scheduler.orchestrator.run_cycle = wrapped_run_cycle
        
        try:
            scheduler.run_forever()
        except KeyboardInterrupt:
            pass
    
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Main thread: update UI
    with Live(_generate_autonomous_status_table(run_count[0], start_time, scheduler), 
              console=console, screen=False, refresh_per_second=1) as live:
        try:
            while scheduler_thread.is_alive():
                live.update(_generate_autonomous_status_table(run_count[0], start_time, scheduler))
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\\n\\n[yellow]Shutdown signal received. Stopping gracefully...[/yellow]")
            console.print("[green]✓ Autonomous mode stopped successfully.[/green]")

@cli.command()
@click.option('--with-ui', is_flag=True, help='Show live status UI while running (like main.py)')
def autonomous(with_ui: bool):
    """
    Launch the system in fully autonomous 24/7 trading mode.
    
    In autonomous mode, the system:
    - Continuously monitors markets 24/7 (US Equity, Crypto, Forex)
    - Automatically selects best market based on hours and performance
    - Runs market scans at adaptive intervals (5-30 min based on activity)
    - Executes trades based on AI agent recommendations
    - Manages positions and enforces risk limits automatically
    - Rotates between markets intelligently
    
    Adaptive Scan Intervals:
    - US Equity (market hours): Every 5 minutes (peak liquidity)
    - Crypto (peak 9am-11pm UTC): Every 15 minutes
    - Crypto (off-peak): Every 30 minutes
    - Forex: Every 10 minutes
    
    Safety Features (Always Active):
    - Paper trading mode (Alpaca paper account)
    - Daily loss limits enforced
    - Maximum position limits enforced
    - Position size limits (2% risk per trade)
    - Automatic error recovery
    
    User Control:
    - Press Ctrl+C at any time to stop gracefully
    - No confirmations required - fully autonomous
    
    Configuration (.env):
    - DRY_RUN=true: Simulate orders (no API calls)
    - DRY_RUN=false: Execute on paper account (recommended)
    - Set MAX_DAILY_TRADES, DAILY_LOSS_LIMIT in .env
    
    Examples:
        # Run with logs only (background-friendly)
        python scripts/run_crew.py autonomous
        
        # Run with live status UI (foreground)
        python scripts/run_crew.py autonomous --with-ui
        
    [Press Ctrl+C to stop]
    """
    if not with_ui:
        # Original behavior - logs only
        console.print(Panel.fit(
            "[bold cyan]🤖 Launching Fully Autonomous 24/7 Trading Mode[/bold cyan]\\n\\n"
            "[green]✓[/green] Multi-market support (US Equity, Crypto, Forex)\\n"
            "[green]✓[/green] Intelligent market rotation\\n"
            "[green]✓[/green] Adaptive scan intervals (5-30 min)\\n"
            "[green]✓[/green] Paper trading with Alpaca\\n"
            "[green]✓[/green] Risk management enforced\\n\\n"
            "[dim]Press Ctrl+C to stop at any time[/dim]",
            border_style="cyan"
        ))
        
        # Show current configuration
        mode = "DRY RUN (simulated)" if settings.dry_run else "PAPER TRADING (Alpaca paper account)"
        console.print(f"\\n[bold]Mode:[/bold] [cyan]{mode}[/cyan]")
        console.print(f"[bold]Max Daily Trades:[/bold] {settings.max_daily_trades}")
        console.print(f"[bold]Daily Loss Limit:[/bold] {settings.daily_loss_limit * 100}%")
        console.print(f"[bold]Max Risk Per Trade:[/bold] {settings.max_risk_per_trade * 100}%\\n")
        
        if not settings.autonomous_mode_enabled:
            console.print("[yellow]Note: AUTONOMOUS_MODE_ENABLED=false in .env. Running unlimited cycles for testing.[/yellow]\\n")
        
        console.print("[bold green]🚀 System starting...[/bold green] (monitoring markets 24/7)\\n")
        
        try:
            scheduler = AutoTradingScheduler()
            scheduler.run_forever()
        except KeyboardInterrupt:
            console.print("\\n\\n[yellow]Shutdown signal received. Stopping gracefully...[/yellow]")
            console.print("[green]✓ Autonomous mode stopped successfully.[/green]")
        except Exception as e:
            console.print(f"\\n[bold red]Error:[/bold red] {str(e)}")
            console.print("[yellow]Check logs/trading_crew_*.log for details[/yellow]")
    else:
        # New behavior - live status UI (from main.py)
        _autonomous_with_ui()

# Cache status to prevent re-initialization in dashboard refresh loop
_cached_status = {
    'alpaca': {'status': '[yellow]Initializing...[/yellow]', 'last_check': 0},
    'gemini': {'status': '[yellow]Initializing...[/yellow]', 'last_check': 0}
}
_STATUS_CACHE_TTL = 30  # Refresh status every 30 seconds instead of every 3 seconds

def get_status_panel() -> Panel:
    """Returns a Panel with the current system status."""
    import time
    current_time = time.time()
    
    table = Table(show_header=False, box=None)
    table.add_column("key", style="cyan")
    table.add_column("value")

    # Check Alpaca status with caching
    if current_time - _cached_status['alpaca']['last_check'] > _STATUS_CACHE_TTL:
        try:
            account = alpaca_manager.get_account()
            equity = account.get('equity')
            if equity is None:
                equity_str = "N/A"
            else:
                equity_str = f"${float(equity):,.2f}"
            _cached_status['alpaca']['status'] = f"[green]Connected[/green] (Equity: {equity_str})"
            _cached_status['alpaca']['last_check'] = current_time
        except Exception as e:
            _cached_status['alpaca']['status'] = f"[red]Connection Failed[/red] ({str(e)[:30]})"
            _cached_status['alpaca']['last_check'] = current_time
    
    alpaca_status = _cached_status['alpaca']['status']

    # Check Gemini status with caching (FIXED: No longer calls get_client() on every refresh)
    if current_time - _cached_status['gemini']['last_check'] > _STATUS_CACHE_TTL:
        try:
            gemini_keys = settings.get_gemini_keys_list()
            # Check if gemini_manager has an existing healthy client (no new connection attempt)
            if hasattr(gemini_manager, '_last_client') and gemini_manager._last_client is not None:
                _cached_status['gemini']['status'] = f"[green]Connected[/green] ({len(gemini_keys)} keys)"
            else:
                # Only initialize connection once (not on every refresh)
                gemini_manager.get_client(skip_health_check=True)
                _cached_status['gemini']['status'] = f"[green]Connected[/green] ({len(gemini_keys)} keys)"
            _cached_status['gemini']['last_check'] = current_time
        except Exception as e:
            _cached_status['gemini']['status'] = f"[red]Connection Failed[/red] ({str(e)[:30]})"
            _cached_status['gemini']['last_check'] = current_time
    
    gemini_status = _cached_status['gemini']['status']

    trading_mode = "[bold yellow]DRY RUN (Simulated)[/bold yellow]" if settings.dry_run else "[bold green]PAPER TRADING (Alpaca Paper)[/bold green]"

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
        table.add_column("Entry", justify="right")
        table.add_column("Current", justify="right")
        table.add_column("P&L", justify="right")

        for pos in positions:
            pl = pos.get('unrealized_pl', 0.0)
            pl_str = f"[green]+${pl:,.2f}[/green]" if pl >= 0 else f"[red]${pl:,.2f}[/red]"
            entry = f"${float(pos.get('avg_entry_price', 0)):,.2f}"
            current = f"${float(pos.get('current_price', 0)):,.2f}"
            table.add_row(pos['symbol'], str(pos['qty']), entry, current, pl_str)

        return Panel(table, title="Open Positions", border_style="yellow")
    except Exception as e:
        return Panel(f"[red]Error fetching positions: {e}[/red]", title="Open Positions", border_style="red")


def get_recent_orders_panel() -> Panel:
    """Returns a Panel with recent orders."""
    try:
        from datetime import timedelta
        orders = alpaca_manager.alpaca_client.get_orders(
            status='all',
            limit=10,
            after=(datetime.now(pytz.utc) - timedelta(days=1)).isoformat()
        )
        
        if not orders:
            return Panel("[dim]No recent orders (last 24h)[/dim]", title="Recent Orders", border_style="blue")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Symbol", style="cyan")
        table.add_column("Side", justify="center")
        table.add_column("Qty", justify="right")
        table.add_column("Status", justify="center")
        
        for order in orders[:5]:  # Show only last 5
            side_color = "green" if order.side == 'buy' else "red"
            status_color = "green" if order.status == 'filled' else "yellow" if order.status == 'pending_new' else "dim"
            table.add_row(
                order.symbol,
                f"[{side_color}]{order.side.upper()}[/{side_color}]",
                str(order.qty),
                f"[{status_color}]{order.status}[/{status_color}]"
            )
        
        return Panel(table, title="Recent Orders (Last 24h)", border_style="blue")
    except Exception as e:
        return Panel(f"[red]Error fetching orders: {e}[/red]", title="Recent Orders", border_style="red")


def get_active_strategies_panel() -> Panel:
    """Returns a Panel with currently active strategies."""
    try:
        # Cache strategies config (no need to reload state every 3 seconds)
        strategies_used = ['3ma', 'rsi_breakout', 'macd', 'bollinger_bands_reversal']  # Default active strategies
        mode = "[bold yellow]DRY RUN[/bold yellow]" if settings.dry_run else "[bold green]PAPER TRADING[/bold green]"
        
        content = f"Mode: {mode}\n\n"
        content += "Active Strategies:\n"
        for strat in strategies_used:
            content += f"  • {strat}\n"
        
        return Panel(content, title="Configuration", border_style="cyan")
    except Exception as e:
        return Panel(f"[red]Error: {e}[/red]", title="Configuration", border_style="red")


def generate_dashboard() -> Layout:
    """Creates the layout for the interactive dashboard."""
    layout = Layout(name="root")

    layout.split(
        Layout(name="header", size=3),
        Layout(ratio=1, name="main"),
        Layout(size=8, name="footer"),
    )

    layout["main"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=1)
    )
    layout["left"].split(Layout(name="status"), Layout(name="strategies"))
    layout["right"].split(Layout(name="positions"), Layout(name="orders"))
    
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

    # Initial render
    layout["header"].update(
        Panel(f"[bold green]🤖 AutoAnalyst - Live Trading Dashboard[/bold green]\n[dim]Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Press Ctrl+C to exit[/dim]", border_style="cyan")
    )
    layout["status"].update(get_status_panel())
    layout["strategies"].update(get_active_strategies_panel())
    layout["positions"].update(get_positions_panel())
    layout["orders"].update(get_recent_orders_panel())

    with Live(layout, screen=True, redirect_stderr=False, refresh_per_second=1) as live:
        try:
            while True:
                time.sleep(3)  # Refresh every 3 seconds
                layout["header"].update(
                    Panel(f"[bold green]🤖 AutoAnalyst - Live Trading Dashboard[/bold green]\n[dim]Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Press Ctrl+C to exit[/dim]", border_style="cyan")
                )
                layout["status"].update(get_status_panel())
                layout["strategies"].update(get_active_strategies_panel())
                layout["positions"].update(get_positions_panel())
                layout["orders"].update(get_recent_orders_panel())
        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard stopped by user.[/yellow]")


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
