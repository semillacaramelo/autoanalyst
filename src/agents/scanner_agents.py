"""
Scanner Agent Definitions
This file provides a class to create all CrewAI agents for the market scanner crew.
"""
from crewai import Agent
from crewai.tools import tool
from src.tools.market_scan_tools import market_scan_tools

@tool("Get S&P 100 Symbols")
def get_sp100_symbols_tool() -> list:
    """Returns the list of S&P 100 symbols."""
    return market_scan_tools.get_sp100_symbols()

@tool("Fetch Universe Data")
def fetch_universe_data_tool(symbols: list) -> dict:
    """Fetch historical OHLCV data for a list of symbols."""
    return market_scan_tools.fetch_universe_data(symbols)

@tool("Analyze Volatility")
def analyze_volatility_tool(symbol_data: dict) -> list:
    """Analyze the volatility of each symbol in the provided data."""
    return market_scan_tools.analyze_volatility(symbol_data)

@tool("Analyze Technical Setup")
def analyze_technical_setup_tool(symbol_data: dict) -> list:
    """Analyze the technical setup of each symbol."""
    return market_scan_tools.analyze_technical_setup(symbol_data)

@tool("Filter by Liquidity")
def filter_by_liquidity_tool(symbol_data: dict) -> list:
    """Filter symbols by their average trading volume."""
    return market_scan_tools.filter_by_liquidity(symbol_data)


class ScannerAgents:
    """A factory class to create scanner agents with a specific LLM."""

    def volatility_analyzer_agent(self, llm) -> Agent:
        return Agent(
            role="Volatility Analyst",
            goal="Analyze the volatility of a universe of stocks to identify assets with profitable trading conditions.",
            backstory="An expert in market volatility, skilled at identifying assets that have enough movement for trading but are not excessively risky.",
            tools=[get_sp100_symbols_tool, fetch_universe_data_tool, analyze_volatility_tool],
            llm=llm,
            verbose=True,
            allow_delegation=False,  # Disable delegation to reduce API calls
            max_iter=3  # Limit iterations to prevent runaway loops
        )

    def technical_setup_agent(self, llm) -> Agent:
        return Agent(
            role="Technical Analyst",
            goal="Evaluate the technical setup of stocks to find assets with strong bullish or bearish signals.",
            backstory="A seasoned chartist who can spot technical patterns and strong signals from a mile away.",
            tools=[analyze_technical_setup_tool],
            llm=llm,
            verbose=True,
            allow_delegation=False,  # Disable delegation to reduce API calls
            max_iter=3  # Limit iterations to prevent runaway loops
        )

    def liquidity_filter_agent(self, llm) -> Agent:
        return Agent(
            role="Liquidity and Risk Analyst",
            goal="Filter out illiquid or hard-to-trade assets to ensure that trading is feasible and cost-effective.",
            backstory="A pragmatic analyst who ensures that every potential trade is backed by sufficient market liquidity.",
            tools=[filter_by_liquidity_tool],
            llm=llm,
            verbose=True,
            allow_delegation=False,  # Disable delegation to reduce API calls
            max_iter=3  # Limit iterations to prevent runaway loops
        )

    def market_intelligence_chief(self, llm) -> Agent:
        return Agent(
            role="Chief of Market Intelligence",
            goal="Synthesize the analyses from the volatility, technical, and liquidity agents to create a prioritized list of top trading opportunities.",
            backstory="The final decision-maker, who weighs all the evidence to identify the most promising assets for the trading crew to focus on.",
            tools=[],
            llm=llm,
            verbose=True,
            allow_delegation=False,  # Disable delegation to reduce API calls
            max_iter=3  # Limit iterations to prevent runaway loops
        )
