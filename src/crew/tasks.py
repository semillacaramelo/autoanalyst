"""
Task Definitions
Sequential tasks for the trading crew workflow.
"""

from crewai import Task
from src.agents.base_agents import (
    data_collector_agent,
    signal_generator_agent,
    signal_validator_agent,
    risk_manager_agent,
    execution_agent
)
from src.config.settings import settings


# Task 1: Data Collection
collect_data_task = Task(
    description="""Fetch historical OHLCV data for {symbol}.
    
    Requirements:
    - Timeframe: {timeframe}
    - Number of bars: {limit}
    - Validate data completeness
    - Check for gaps, NaN values, and OHLC consistency
    
    Return the data result including validation status.""",
    expected_output="""A dictionary containing:
    - success: Boolean
    - data: DataFrame with OHLCV data
    - metadata: Includes validation results and bar count
    
    Example:
    {{
        "success": true,
        "data": <DataFrame>,
        "metadata": {{
            "symbol": "SPY",
            "bars_fetched": 100,
            "validation": {{"is_valid": true}}
        }}
    }}""",
    agent=data_collector_agent
)


# Task 2: Signal Generation
generate_signal_task = Task(
    description="""Analyze the market data and generate a trading signal using the 3MA strategy.
    
    Strategy Rules:
    - Calculate Fast ({ma_fast}), Medium ({ma_medium}), and Slow ({ma_slow}) EMAs
    - BUY: Fast MA crosses above Medium MA AND Medium MA > Slow MA
    - SELL: Fast MA crosses below Medium MA AND Medium MA < Slow MA
    - HOLD: Any other condition
    
    Clearly explain your reasoning and the indicator values.""",
    expected_output="""A dictionary with the trading signal:
    {{
        "signal": "BUY" | "SELL" | "HOLD",
        "fast_ma": <float>,
        "medium_ma": <float>,
        "slow_ma": <float>,
        "current_price": <float>,
        "fast_crossed_above": <boolean>,
        "fast_crossed_below": <boolean>
    }}""",
    agent=signal_generator_agent,
    context=[collect_data_task]  # Depends on data collection
)


# Task 3: Signal Validation
validate_signal_task = Task(
    description="""Validate the generated signal using confirmation layers.
    
    Confirmation Checks:
    1. Volume Confirmation: Current volume > {volume_threshold}x average
    2. Volatility Check: ATR within acceptable range (0.3 - 2.0)
    3. Trend Strength: ADX > {adx_threshold}
    
    Rules:
    - If signal is BUY or SELL, check all confirmations
    - If fewer than 2 confirmations pass, override signal to HOLD
    - If signal is already HOLD, keep it as HOLD
    
    Provide detailed reasoning for your decision.""",
    expected_output="""A validated signal with confirmation details:
    {{
        "final_signal": "BUY" | "SELL" | "HOLD",
        "original_signal": "<from previous task>",
        "confirmations_passed": ["volume", "volatility", "trend"],
        "override_applied": <boolean>,
        "override_reason": "<explanation if overridden>"
    }}""",
    agent=signal_validator_agent,
    context=[generate_signal_task]
)


# Task 4: Risk Management
assess_risk_task = Task(
    description="""Perform risk management checks and calculate position size.
    
    Portfolio Constraints:
    - Max open positions: {max_positions}
    - Max risk per trade: {max_risk}%
    - Daily loss limit: {daily_loss}%
    
    Steps:
    1. Check if portfolio constraints allow new trades
    2. If signal is HOLD, skip position sizing
    3. If signal is BUY/SELL, calculate position size based on:
       - Current price
       - ATR (volatility)
       - Account equity
    4. Provide trade approval or rejection with clear reasoning""",
    expected_output="""Risk assessment and position sizing:
    {{
        "trade_approved": <boolean>,
        "signal": "BUY" | "SELL" | "HOLD",
        "position_size": <int> shares,
        "risk_checks": {{
            "max_positions": "PASS" | "FAIL",
            "daily_loss": "PASS" | "FAIL",
            "account_status": "PASS" | "FAIL"
        }},
        "veto_reason": "<explanation if rejected>"
    }}""",
    agent=risk_manager_agent,
    context=[validate_signal_task]
)


# Task 5: Execution
execute_trade_task = Task(
    description="""Execute the approved trade (if any).
    
    Rules:
    - If trade_approved is False, do not execute
    - If signal is HOLD, do not execute
    - If signal is BUY or SELL and approved, place market order for {symbol}
    
    Execution Steps:
    1. Verify trade approval status
    2. Place market order with calculated position size
    3. Confirm order submission
    4. Log the order ID and execution details
    
    In DRY_RUN mode, simulate the order and log what would have been executed.""",
    expected_output="""Execution summary:
    {{
        "execution_status": "SUCCESS" | "SKIPPED" | "FAILED",
        "order_id": "<alpaca order ID or 'DRY_RUN'>",
        "symbol": "{symbol}",
        "side": "BUY" | "SELL",
        "qty": <int>,
        "reason": "<explanation for execution or skip>",
        "timestamp": "<ISO timestamp>"
    }}""",
    agent=execution_agent,
    context=[assess_risk_task]
)


# Export all tasks
__all__ = [
    'collect_data_task',
    'generate_signal_task',
    'validate_signal_task',
    'assess_risk_task',
    'execute_trade_task'
]
