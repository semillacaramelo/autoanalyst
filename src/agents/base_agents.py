"""
Agent Definitions Factory
This file provides a class to create all CrewAI agents for the trading system,
ensuring the correct LLM is injected into each one.

Note: Agents expect the provided `llm` object to be an adapter that exposes
provider metadata (e.g. `provider == 'google'`, `model == 'google/...') and
delegates generation calls to an underlying LangChain or provider client. Use
`src.connectors.gemini_connector.gemini_manager.get_adapter()` to obtain the
correct adapter instance.
"""

from crewai import Agent
from crewai.tools import tool
from src.tools.market_data_tools import market_data_tools
from src.tools.analysis_tools import technical_analysis
from src.tools.execution_tools import execution_tools
from src.crew.crew_context import crew_context

# Tool definitions remain the same
@tool("Fetch OHLCV Data")
def fetch_ohlcv_data_tool(symbol: str, timeframe: str = "1Min", limit: int = 100) -> dict:
    """Fetch historical OHLCV data."""
    result = market_data_tools.fetch_ohlcv_data(symbol, timeframe, limit)
    if result.get('success') and result.get('data') is not None:
        crew_context.market_data = result['data']
    return result

from src.strategies.registry import get_strategy

@tool("Generate Trading Signal")
def generate_signal_tool(strategy_name: str) -> dict:
    """
    Generate a trading signal using a specified strategy.

    Args:
        strategy_name: The name of the strategy to use (e.g., '3ma', 'rsi_breakout').
    """
    df = crew_context.market_data
    if df is None or df.empty:
        return {"signal": "HOLD", "error": "No data available"}

    try:
        strategy = get_strategy(strategy_name)
        signal = strategy.generate_signal(df)
        validated_signal = strategy.validate_signal(df, signal)
        return validated_signal
    except Exception as e:
        return {"signal": "HOLD", "error": str(e)}


@tool("Check Portfolio Constraints")
def check_constraints_tool() -> dict:
	"""Check portfolio risk constraints."""
	return execution_tools.check_portfolio_constraints()

@tool("Calculate Position Size")
def calculate_position_size_tool(signal: str, current_price: float, atr: float, account_equity: float) -> dict:
	"""Calculate position size based on risk."""
	return execution_tools.calculate_position_size(signal, current_price, atr, account_equity)

@tool("Place Market Order")
def place_order_tool(symbol: str, qty: int, side: str) -> dict:
	"""Place a market order."""
	return execution_tools.place_order(symbol, qty, side)


class TradingAgents:
    """A factory class to create trading agents with a specific LLM."""

    def data_collector_agent(self, llm) -> Agent:
        return Agent(
            role="Market Data Specialist",
            goal="Fetch accurate, complete OHLCV data for the specified asset and validate its quality",
            backstory="A meticulous data collector ensuring every bar is complete and validated.",
            tools=[fetch_ohlcv_data_tool],
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

    def signal_generator_agent(self, llm) -> Agent:
        return Agent(
            role="Quantitative Technical Analyst",
            goal="Dynamically apply a selected trading strategy to generate and validate a trading signal",
            backstory="A flexible analyst capable of applying various quantitative strategies to market data.",
            tools=[generate_signal_tool],
            llm=llm,
            verbose=True,
            allow_delegation=False
        )


    def risk_manager_agent(self, llm) -> Agent:
        return Agent(
            role="Portfolio Risk Officer",
            goal="Enforce position sizing and portfolio-level risk constraints to protect capital",
            backstory="The guardian of capital, enforcing strict risk rules on every potential trade.",
            tools=[
                check_constraints_tool,
                calculate_position_size_tool
            ],
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

    def execution_agent(self, llm) -> Agent:
        return Agent(
            role="Head of Trading Desk",
            goal="Execute approved trades with precision and verify successful order placement",
            backstory="A cool-headed execution specialist who translates approved decisions into live market orders.",
            tools=[place_order_tool],
            llm=llm,
            verbose=True,
            allow_delegation=False
        )