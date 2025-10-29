"""
Base Agent Definitions
All CrewAI agents for the trading system.
"""

from crewai import Agent
from src.connectors.gemini_connector import gemini_manager
from src.tools.market_data_tools import market_data_tools
from src.tools.analysis_tools import technical_analysis
from src.tools.execution_tools import execution_tools
from crewai_tools import tool
import logging

logger = logging.getLogger(__name__)


# ============================================
# CREWAI TOOL WRAPPERS
# ============================================
# CrewAI requires tools to be decorated with @tool

@tool("Fetch OHLCV Data")
def fetch_ohlcv_data_tool(symbol: str, timeframe: str = "1Min", limit: int = 100) -> dict:
	"""
	Fetch historical OHLCV (Open, High, Low, Close, Volume) data for analysis.
    
	Args:
		symbol: Stock symbol (e.g., 'SPY')
		timeframe: Bar timeframe ('1Min', '5Min', '1Hour')
		limit: Number of bars to fetch
    
	Returns:
		Dictionary with success status, data, and metadata
	"""
	return market_data_tools.fetch_ohlcv_data(symbol, timeframe, limit)


@tool("Generate 3MA Signal")
def generate_3ma_signal_tool(data: dict) -> dict:
	"""
	Generate trading signal using Triple Moving Average strategy.
    
	Args:
		data: Result from fetch_ohlcv_data_tool containing DataFrame
    
	Returns:
		Dictionary with signal ('BUY', 'SELL', 'HOLD') and indicator values
	"""
	if data.get('success') and data.get('data') is not None:
		df = data['data']
		return technical_analysis.generate_3ma_signal(df)
	else:
		return {"signal": "HOLD", "error": "No data available"}


@tool("Check Volume Confirmation")
def check_volume_confirmation_tool(data: dict) -> dict:
	"""
	Check if current volume confirms the signal strength.
    
	Args:
		data: Result from fetch_ohlcv_data_tool
    
	Returns:
		Dictionary with confirmation status and volume metrics
	"""
	if data.get('success') and data.get('data') is not None:
		df = data['data']
		return technical_analysis.calculate_volume_confirmation(df)
	else:
		return {"confirmed": False, "error": "No data available"}


@tool("Check Volatility Range")
def check_volatility_tool(data: dict) -> dict:
	"""
	Check if volatility (ATR) is within acceptable trading range.
    
	Args:
		data: Result from fetch_ohlcv_data_tool
    
	Returns:
		Dictionary with volatility check results
	"""
	if data.get('success') and data.get('data') is not None:
		df = data['data']
		return technical_analysis.calculate_volatility_check(df)
	else:
		return {"acceptable": False, "error": "No data available"}


@tool("Check Trend Strength")
def check_trend_strength_tool(data: dict) -> dict:
	"""
	Check if the market has a strong trend using ADX.
    
	Args:
		data: Result from fetch_ohlcv_data_tool
    
	Returns:
		Dictionary with trend strength analysis
	"""
	if data.get('success') and data.get('data') is not None:
		df = data['data']
		return technical_analysis.calculate_trend_strength(df)
	else:
		return {"has_strong_trend": False, "error": "No data available"}


@tool("Check Portfolio Constraints")
def check_constraints_tool() -> dict:
	"""
	Check if portfolio constraints allow opening new positions.
	Validates max positions, daily loss limit, and account status.
    
	Returns:
		Dictionary with approval status and detailed checks
	"""
	return execution_tools.check_portfolio_constraints()


@tool("Calculate Position Size")
def calculate_position_size_tool(
	signal: str,
	current_price: float,
	atr: float,
	account_equity: float
) -> dict:
	"""
	Calculate optimal position size based on risk management rules.
    
	Args:
		signal: Trading signal ('BUY' or 'SELL')
		current_price: Current asset price
		atr: Average True Range (volatility)
		account_equity: Total account equity
    
	Returns:
		Dictionary with position size and risk metrics
	"""
	return execution_tools.calculate_position_size(
		signal, current_price, atr, account_equity
	)


@tool("Place Market Order")
def place_order_tool(symbol: str, qty: int, side: str) -> dict:
	"""
	Place a market order for the specified symbol.
    
	Args:
		symbol: Stock symbol (e.g., 'SPY')
		qty: Number of shares
		side: 'BUY' or 'SELL'
    
	Returns:
		Dictionary with order execution result
	"""
	return execution_tools.place_order(symbol, qty, side)


# ============================================
# AGENT DEFINITIONS
# ============================================

data_collector_agent = Agent(
	role="Market Data Specialist",
	goal="Fetch accurate, complete OHLCV data for the specified asset and validate its quality",
	backstory="""You are a meticulous data collector with an obsession for data quality.
	You ensure every bar is complete, validated, and ready for analysis.
	You never pass incomplete or suspicious data to the next agent.""",
	tools=[fetch_ohlcv_data_tool],
verbose=True,
allow_delegation=False
)


signal_generator_agent = Agent(
	role="Quantitative Technical Analyst",
	goal="Calculate precise technical indicators and generate trading signals using the 3MA strategy",
	backstory="""You are a mathematician and technical analysis expert.
	You live and breathe charts, moving averages, and indicators.
	Your calculations are always precise, and you clearly explain your signal generation logic.""",
	tools=[generate_3ma_signal_tool],
	verbose=True,
	allow_delegation=False
)


signal_validator_agent = Agent(
	role="Chief Quality Officer",
	goal="Validate trading signals using multiple confirmation layers (volume, volatility, trend strength)",
	backstory="""You are a skeptical analyst who trusts no signal until proven by multiple confirmations.
	You apply volume confirmation, volatility filters, and trend strength analysis.
	If a signal doesn't meet your strict criteria, you override it to HOLD.
	Your conservative approach protects capital from false signals.""",
	tools=[
		check_volume_confirmation_tool,
		check_volatility_tool,
		check_trend_strength_tool
	],
	verbose=True,
	allow_delegation=False
)


risk_manager_agent = Agent(
	role="Portfolio Risk Officer",
	goal="Enforce position sizing and portfolio-level risk constraints to protect capital",
	backstory="""You are the guardian of capital. No trade is worth risking the entire portfolio.
	You calculate optimal position sizes based on volatility (ATR) and enforce strict limits:
	- Maximum risk per trade
	- Maximum open positions
	- Daily loss limits
	You have veto power over any trade that violates risk rules.""",
	tools=[
		check_constraints_tool,
		calculate_position_size_tool
	],
	verbose=True,
	allow_delegation=False
)


execution_agent = Agent(
	role="Head of Trading Desk",
	goal="Execute approved trades with precision and verify successful order placement",
	backstory="""You are a cool-headed execution specialist.
	Once a trade is approved, you act with speed and precision.
	You translate decisions into live market orders and confirm execution.
	You never hesitate, but you also never execute unapproved trades.""",
	tools=[place_order_tool],
	verbose=True,
	allow_delegation=False
)


logger.info("All agents initialized successfully")
