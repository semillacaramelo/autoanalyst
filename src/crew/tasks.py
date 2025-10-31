"""
Task Definitions for the Trading Crew
This file defines a class that creates and new_configs all tasks for the agents.
"""

from crewai import Task

class TradingTasks:
    """A factory class for creating all trading-related tasks."""

    def collect_data_task(self, agent) -> Task:
        return Task(
            description="""Fetch historical OHLCV data for {symbol}.
            
            Requirements:
            - Timeframe: {timeframe}
            - Number of bars: {limit}
            - Validate data completeness and consistency.
            
            Return the data result including validation status.""",
            expected_output="""A dictionary containing the success status, a pandas DataFrame with the OHLCV data, and metadata including validation results.""",
            agent=agent
        )

    def generate_signal_task(self, agent, context) -> Task:
        return Task(
            description="""Analyze the market data from the previous step and generate a trading signal using the '{strategy_name}' strategy.
            
            The tool will handle the specific rules of the chosen strategy, including signal generation and validation.
            
            Your role is to ensure the correct strategy name is passed to the tool and to clearly report the results provided.
            """,
            expected_output="""A dictionary with the final validated signal ('BUY', 'SELL', or 'HOLD'), the confidence level, and detailed results from the strategy's execution.""",
            agent=agent,
            context=context
        )

    def assess_risk_task(self, agent, context) -> Task:
        return Task(
            description="""Perform risk management checks and calculate the appropriate position size for the validated signal.
            
            Portfolio Constraints:
            - Max open positions: {max_positions}
            - Max risk per trade: {max_risk}%
            - Daily loss limit: {daily_loss}%
            
            Steps:
            1. Check if portfolio constraints (max positions, daily loss) allow a new trade.
            2. If the signal is HOLD, or if constraints fail, approve no trade.
            3. If a BUY/SELL signal is approved, calculate position size based on volatility (ATR) and account equity.
            
            Provide a clear approval or rejection decision with reasoning.""",
            expected_output="""A dictionary indicating whether the trade is approved, the calculated position size (in shares), and the status of all risk checks.""",
            agent=agent,
            context=context
        )

    def execute_trade_task(self, agent, context) -> Task:
        return Task(
            description="""Execute the trade if it was approved by the Risk Manager.
            
            Rules:
            - If the trade was not approved, or the signal is HOLD, do nothing.
            - If a BUY or SELL trade is approved, place a market order for the calculated position size.
            
            In DRY_RUN mode, simulate the order and log what would have been executed.""",
            expected_output="""A dictionary summarizing the execution status ('SUCCESS', 'SKIPPED', 'FAILED'), including the order ID (or a simulation notice) and trade details.""",
            agent=agent,
            context=context
        )
