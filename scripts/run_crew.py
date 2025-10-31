#!/usr/bin/env python3
"""
Trading Crew CLI
Command-line interface for running the trading crew and market scanner.
"""

import click
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from pathlib import Path
import sys

# Add src to path before other project imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.crew.trading_crew import trading_crew
from src.crew.market_scanner_crew import market_scanner_crew
from src.connectors.alpaca_connector import alpaca_manager
from src.utils.logger import setup_logging

console = Console()


@click.group()
def cli():
    """AI-Driven Trading Crew - Backend CLI"""
    pass


@cli.command()
@click.option('--symbol', default=None, help='Stock symbol to trade (default: from config)')
@click.option('--strategy', default='3ma', help='Strategy to use (3ma, rsi_breakout, etc.)')
@click.option('--timeframe', default='1Min', help='Bar timeframe (1Min, 5Min, etc.)')
@click.option('--limit', default=100, help='Number of historical bars to fetch')
def run(symbol, strategy, timeframe, limit):
    """Run the trading crew for a single execution."""
    console.print(Panel.fit(
        "[bold cyan]AI-Driven Trading Crew[/bold cyan]\n"
        "[dim]Backend-First Development Version[/dim]",
        border_style="cyan"
    ))
    
    console.print("\n[yellow]Configuration:[/yellow]")
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
def scan():
    """Run the market scanner crew to find opportunities."""
    console.print(Panel.fit(
        "[bold cyan]Market Scanner Crew[/bold cyan]",
        border_style="cyan"
    ))
    console.print("\n[cyan]Scanning the S&P 100 for trading opportunities...[/cyan]\n")

    try:
        # The result from the crew is a string, which we need to parse.
        # CrewAI's output format can sometimes be markdown with a JSON block.
        raw_result = market_scanner_crew.run()

        # Clean up the raw result to extract the JSON part
        json_string = raw_result.strip()
        if json_string.startswith("```json"):
            json_string = json_string[7:]
        if json_string.endswith("```"):
            json_string = json_string[:-3]

        # Parse the JSON
        scan_data = json.loads(json_string)

        console.print(Panel.fit(
            "[bold green]✓ Market scan completed successfully![/bold green]",
            border_style="green"
        ))

        console.print("\n[yellow]Scan Results:[/yellow]")
        # Using Syntax to pretty-print the JSON
        syntax = Syntax(json.dumps(scan_data, indent=2), "json", theme="solarized-dark", line_numbers=True)
        console.print(syntax)

    except json.JSONDecodeError:
        console.print(Panel.fit(
            "[bold red]✗ Failed to parse scanner output[/bold red]",
            border_style="red"
        ))
        console.print("\n[yellow]Raw Output:[/yellow]")
        console.print(raw_result)
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]✗ Unexpected error during scan[/bold red]\n"
            f"[dim]{str(e)}[/dim]",
            border_style="red"
        ))

@cli.command()
def status():
    """Check system status and connectivity."""
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


@cli.command()
def validate():
    """Run configuration validation checks."""
    import subprocess
    script_path = Path(__file__).parent / "validate_config.py"
    subprocess.run(["python", str(script_path)])


if __name__ == '__main__':
    cli()
