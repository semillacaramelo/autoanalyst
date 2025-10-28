from crewai import Task
from agents.trading_agents import asset_selector, trend_analyzer, signal_confirmer, trade_executor

# Define the tasks for the agents
select_asset_task = Task(
    description="Select the best asset to trade from the list {assets_of_interest} based on current market volume and volatility.",
    expected_output="The ticker symbol of a single asset to trade (e.g., 'SPY').",
    agent=asset_selector
)

analyze_trend_task = Task(
    description="Analyze the 1-minute chart for the selected asset using the 3 MA strategy. Generate a 'BUY', 'SELL', or 'HOLD' signal.",
    expected_output="A JSON object containing the asset symbol, the signal ('BUY', 'SELL', 'HOLD'), and the current price.",
    context=[select_asset_task], # Depends on the asset selected
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
