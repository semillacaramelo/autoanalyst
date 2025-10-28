from crewai import Task
from typing import Dict

def get_trading_tasks(agents: Dict[str, any]):
    """
    Creates and returns all the trading tasks.
    This function is designed for lazy initialization of tasks and requires
    the agent dictionary to be passed as an argument.
    """
    asset_selector = agents['asset_selector']
    trend_analyzer = agents['trend_analyzer']
    signal_confirmer = agents['signal_confirmer']
    trade_executor = agents['trade_executor']

    select_asset_task = Task(
        description="Select the best asset to trade from the list {assets_of_interest} based on current market volume and volatility.",
        expected_output="The ticker symbol of a single asset to trade (e.g., 'SPY').",
        agent=asset_selector
    )

    analyze_trend_task = Task(
        description="""Analyze the 1-minute chart for the asset provided in the context. First, use the fetch_historical_data tool to get data from {start_date} to {end_date}. Then, use the calculate_3ma_signal tool on that data to generate a 'BUY', 'SELL', or 'HOLD' signal.""",
        expected_output="A JSON object containing the asset symbol, the signal ('BUY', 'SELL', 'HOLD'), and the latest closing price.",
        context=[select_asset_task],
        agent=trend_analyzer
    )

    confirm_signal_task = Task(
        description="Confirm the trade signal's quality. Check for abnormal volatility or conflicting market indicators. If the risk is too high, override the signal to 'HOLD'.",
        expected_output="A final, validated JSON signal object, possibly overriding the original.",
        context=[analyze_trend_task],
        agent=signal_confirmer
    )

    execute_trade_task = Task(
        description="Execute the confirmed trade signal. If the signal is 'BUY' or 'SELL', place a market order for 10 shares. Otherwise, do nothing.",
        expected_output="A confirmation message with the Alpaca order ID if a trade was placed, or 'No trade executed'.",
        context=[confirm_signal_task],
        agent=trade_executor
    )

    return [
        select_asset_task,
        analyze_trend_task,
        confirm_signal_task,
        execute_trade_task,
    ]
