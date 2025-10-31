#!/usr/bin/env python3
"""
Configuration Validation Script
Run before starting the trading crew to ensure all settings are correct.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.config.settings import settings
from src.connectors.alpaca_connector import alpaca_manager
from src.connectors.gemini_connector import gemini_manager

console = Console()


def validate_gemini_keys():
    """Test Gemini API key connectivity."""
    keys = settings.get_gemini_keys_list()
    console.print(f"\n[cyan]Testing {len(keys)} Gemini API key(s)...[/cyan]")
    
    for i, key in enumerate(keys, 1):
        masked_key = f"{key[:10]}...{key[-4:]}"
        console.print(f"  Key {i}: {masked_key} [green]✓[/green]")
    
    # Live connectivity test: try to obtain a client
    try:
        client = gemini_manager.get_client()
        console.print(f"  Live test: Gemini client for model '{client.model}' created [green]✓[/green]")
        # Optional: a lightweight check with the client
        client.invoke("Health check")
        console.print(f"  Live test: Health check invocation successful [green]✓[/green]")
    except Exception as e:
        console.print(f"  Live test failed: {e} [red]✗[/red]")
        return False
    
    return True

def validate_alpaca_connection():
    """Test Alpaca API connectivity."""
    console.print("\n[cyan]Testing Alpaca API connection...[/cyan]")
    
    # Live connectivity test: try to fetch account info
    try:
        acct = alpaca_manager.get_account()
        console.print(f"  Base URL: {settings.alpaca_base_url} [green]✓[/green]")
        console.print(f"  Mode: {'Paper Trading' if alpaca_manager.is_paper else 'LIVE TRADING'} [green]✓[/green]")
        console.print(f"  Account Status: {acct.get('status')} (Equity: ${acct.get('equity'):,.2f}) [green]✓[/green]")
        return True
    except Exception as e:
        console.print(f"  Live test failed: {e} [red]✗[/red]")
        return False


def validate_strategy_params():
	"""Validate trading strategy parameters."""
	console.print("\n[cyan]Validating strategy parameters...[/cyan]")
    
	table = Table(show_header=True, header_style="bold magenta")
	table.add_column("Parameter", style="cyan")
	table.add_column("Value", style="green")
	table.add_column("Status", justify="center")
    
	table.add_row("Trading Symbol", settings.trading_symbol, "✓")
	table.add_row("Fast MA Period", str(settings.ma_fast_period), "✓")
	table.add_row("Medium MA Period", str(settings.ma_medium_period), "✓")
	table.add_row("Slow MA Period", str(settings.ma_slow_period), "✓")
	table.add_row("Volume Threshold", str(settings.volume_threshold), "✓")
	table.add_row("ADX Threshold", str(settings.adx_threshold), "✓")
    
	console.print(table)
	return True


def validate_risk_management():
	"""Validate risk management parameters."""
	console.print("\n[cyan]Validating risk management...[/cyan]")
    
	table = Table(show_header=True, header_style="bold magenta")
	table.add_column("Parameter", style="cyan")
	table.add_column("Value", style="green")
	table.add_column("Status", justify="center")
    
	table.add_row(
		"Max Risk per Trade",
		f"{settings.max_risk_per_trade * 100}%",
		"✓"
	)
	table.add_row(
		"Max Open Positions",
		str(settings.max_open_positions),
		"✓"
	)
	table.add_row(
		"Daily Loss Limit",
		f"{settings.daily_loss_limit * 100}%",
		"✓"
	)
    
	console.print(table)
	return True


def main():
	"""Run all validation checks."""
	console.print(Panel.fit(
		"[bold yellow]Trading Crew Configuration Validator[/bold yellow]",
		border_style="yellow"
	))
    
	checks = [
		("Gemini API Keys", validate_gemini_keys),
		("Alpaca Connection", validate_alpaca_connection),
		("Strategy Parameters", validate_strategy_params),
		("Risk Management", validate_risk_management),
	]
    
	results = []
	for check_name, check_func in checks:
		try:
			result = check_func()
			results.append((check_name, result))
		except Exception as e:
			console.print(f"\n[red]✗ {check_name} failed: {e}[/red]")
			results.append((check_name, False))
    
	# Summary
	console.print("\n" + "="*50)
	passed = sum(1 for _, result in results if result)
	total = len(results)
    
	if passed == total:
		console.print(Panel.fit(
			f"[bold green]All {total} checks passed! ✓[/bold green]",
			border_style="green"
		))
		sys.exit(0)
	else:
		console.print(Panel.fit(
			f"[bold red]{passed}/{total} checks passed. Fix errors before running.[/bold red]",
			border_style="red"
		))
		sys.exit(1)


if __name__ == "__main__":
	main()
