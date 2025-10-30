"""
Task Definitions for the Trading Crew
This file defines a class that creates and configures all tasks for the agents.
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
            - Use the shared context: {context}
            
            Return the data result including validation status.""",
            expected_output="""A dictionary containing the success status, a pandas DataFrame with the OHLCV data, and metadata including validation results.""",
            agent=agent
        )

    def generate_signal_task(self, agent, context) -> Task:
        return Task(
            description="""Analyze the market data from the previous step and generate a trading signal using the 3MA strategy.
            Use the shared context to access market data: {context}
            
            Strategy Rules:
            - Calculate Fast ({ma_fast}), Medium ({ma_medium}), and Slow ({ma_slow}) EMAs.
            - BUY Signal: Fast MA crosses above Medium MA AND Medium MA > Slow MA.
            - SELL Signal: Fast MA crosses below Medium MA AND Medium MA < Slow MA.
            - HOLD: Any other condition.
            
            Clearly explain your reasoning and the indicator values.""",
            expected_output="""A dictionary with the trading signal ('BUY', 'SELL', or 'HOLD') and the calculated moving average values.""",
            agent=agent,
            context=[context]
        )

    def validate_signal_task(self, agent, context) -> Task:
        return Task(
            description="""Validate the generated signal using multiple confirmation layers.
            Use the shared context to access market data: {context}
            
            Confirmation Checks:
            1. Volume: Current volume > {volume_threshold}x average.
            2. Volatility: ATR is within an acceptable range (e.g., 0.3 - 2.0).
            3. Trend Strength: ADX > {adx_threshold}.
            
            Rules:
            - A BUY or SELL signal requires at least 2 out of 3 confirmations to pass.
            - If confirmations are not met, the signal must be overridden to HOLD.
            
            Provide detailed reasoning for the final decision.""",
            expected_output="""A dictionary with the final validated signal ('BUY', 'SELL', or 'HOLD'), a list of the confirmations that passed, and a reason if the signal was overridden.""",
            agent=agent,
            context=[context]
        )

    def assess_risk_task(self, agent, context) -> Task:
        return Task(
            description="""Perform risk management checks and calculate the appropriate position size for the validated signal.
            Use the shared context to access market data: {context}
            
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
            context=[context]
        )

    def execute_trade_task(self, agent, context) -> Task:
        return Task(
            description="""Execute the trade if it was approved by the Risk Manager.
            Use the shared context to access market data: {context}
            
            Rules:
            - If the trade was not approved, or the signal is HOLD, do nothing.
            - If a BUY or SELL trade is approved, place a market order for the calculated position size.
            
            In DRY_RUN mode, simulate the order and log what would have been executed.""",
            expected_output="""A dictionary summarizing the execution status ('SUCCESS', 'SKIPPED', 'FAILED'), including the order ID (or a simulation notice) and trade details.""",
            agent=agent,
            context=[context]
        )