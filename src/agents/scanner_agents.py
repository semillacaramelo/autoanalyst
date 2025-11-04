"""
Scanner Agent Definitions

✅ PHASE 4 REFACTORED (November 4, 2025)

STATUS: FUNCTIONAL - Tools refactored to use Independent Tool Fetching pattern
CHANGE: Tools now accept List[str] (symbol names) instead of Dict[str, DataFrame]
RESULT: Compatible with CrewAI's JSON serialization architecture

REFACTORING COMPLETED:
- analyze_volatility_tool: Now accepts symbols list, fetches data internally
- analyze_technical_setup_tool: Now accepts symbols list, fetches data internally
- filter_by_liquidity_tool: Now accepts symbols list, fetches data internally
- fetch_universe_data_tool: Marked deprecated, kept for backwards compatibility

See docs/CREWAI_REFERENCE.md for architecture patterns.

This file provides a class to create all CrewAI agents for the market scanner crew.
"""
from crewai import Agent
from crewai.tools import tool
from src.tools.market_scan_tools import market_scan_tools
from typing import Optional, List

@tool("Get S&P 100 Symbols")
def get_sp100_symbols_tool() -> list:
    """Returns the list of S&P 100 symbols."""
    return market_scan_tools.get_sp100_symbols()

@tool("Get Universe Symbols")
def get_universe_symbols_tool(market: str = "US_EQUITY", max_symbols: int = None) -> list:
    """
    Get trading universe symbols for a specific market.
    
    Args:
        market: Market to scan ('US_EQUITY', 'CRYPTO', 'FOREX'). Defaults to 'US_EQUITY'
        max_symbols: Maximum number of symbols to return. Use 0 or leave empty for all symbols
    
    Returns:
        List of symbols from the specified universe
    """
    # Convert 0 to None for "all symbols"
    max_syms = None if max_symbols == 0 or max_symbols is None else max_symbols
    return market_scan_tools.get_universe_symbols(market, max_syms)

@tool("Analyze Volatility")
def analyze_volatility_tool(
    symbols: List[str],
    timeframe: str = "1Hour",
    limit: int = 100
) -> list:
    """
    Analyze the volatility of symbols (Independent Tool Fetching pattern).
    
    ✅ PHASE 4 REFACTORED: Tool fetches its own data internally.
    
    Args:
        symbols: List of symbol strings (e.g., ['SPY', 'AAPL', 'BTC/USD'])
        timeframe: Bar timeframe for volatility calculation (default: '1Hour')
        limit: Number of bars to fetch (default: 100)
    
    Returns:
        List of dicts with volatility metrics (ATR, scores, status)
    """
    return market_scan_tools.analyze_volatility(symbols, timeframe, limit)

@tool("Analyze Technical Setup")
def analyze_technical_setup_tool(
    symbols: List[str],
    timeframe: str = "1Day",
    limit: int = 100
) -> list:
    """
    Analyze the technical setup of symbols (Independent Tool Fetching pattern).
    
    ✅ PHASE 4 REFACTORED: Tool fetches its own data internally.
    
    Args:
        symbols: List of symbol strings to analyze
        timeframe: Bar timeframe for analysis (default: '1Day')
        limit: Number of bars to fetch (default: 100)
    
    Returns:
        List of dicts with technical scores, indicators, and reasoning
    """
    return market_scan_tools.analyze_technical_setup(symbols, timeframe, limit)

@tool("Filter By Liquidity")
def filter_by_liquidity_tool(
    symbols: List[str],
    min_volume: int = 1_000_000,
    timeframe: str = "1Day",
    limit: int = 30
) -> list:
    """
    Filter symbols by average trading volume (Independent Tool Fetching pattern).
    
    ✅ PHASE 4 REFACTORED: Tool fetches its own data internally.
    
    Args:
        symbols: List of symbol strings to filter
        min_volume: Minimum average daily volume (default: 1M)
        timeframe: Bar timeframe for volume calculation (default: '1Day')
        limit: Number of bars to average (default: 30)
    
    Returns:
        List of dicts with liquidity scores and filtering results
    """
    return market_scan_tools.filter_by_liquidity(symbols, min_volume, timeframe, limit)

@tool("Fetch Universe Data - DEPRECATED")
def fetch_universe_data_tool(symbols: list, timeframe: str = "1Day", limit: int = 100, asset_class: Optional[str] = None) -> dict:
    """
    ⚠️  DEPRECATED - DO NOT USE IN CREWAI WORKFLOWS
    
    This tool returns DataFrames which cannot be passed to other tools due to
    CrewAI's JSON serialization. Use the refactored tools instead:
    - analyze_volatility_tool(symbols)
    - analyze_technical_setup_tool(symbols)
    - filter_by_liquidity_tool(symbols)
    
    Kept for backwards compatibility and testing only.
    """
    return market_scan_tools.fetch_universe_data(symbols, timeframe, limit, asset_class)


class ScannerAgents:
    """A factory class to create scanner agents with a specific LLM."""

    def volatility_analyzer_agent(self, llm, target_market: str = "US_EQUITY") -> Agent:
        """
        Create a volatility analyzer agent for a specific market.
        
        ✅ PHASE 4 UPDATED: Agent now uses refactored tools (accepts symbol lists)
        
        Args:
            llm: Language model for the agent
            target_market: Market to analyze ('US_EQUITY', 'CRYPTO', 'FOREX')
        """
        market_context = self._get_market_context(target_market)
        
        return Agent(
            role="Volatility Analyst",
            goal=f"Analyze the volatility of {market_context['asset_type']} to identify assets with profitable trading conditions.",
            backstory=f"An expert in {market_context['name']} market volatility, skilled at identifying assets that have enough movement for trading but are not excessively risky. {market_context['specifics']}",
            tools=[get_universe_symbols_tool, analyze_volatility_tool],
            llm=llm,
            verbose=True,
            allow_delegation=False,  # Disable delegation to reduce API calls
            max_iter=3  # Limit iterations to prevent runaway loops
        )

    def technical_setup_agent(self, llm, target_market: str = "US_EQUITY") -> Agent:
        """
        Create a technical analyst agent for a specific market.
        
        ✅ PHASE 4 UPDATED: Agent now uses refactored tools (accepts symbol lists)
        
        Args:
            llm: Language model for the agent
            target_market: Market to analyze ('US_EQUITY', 'CRYPTO', 'FOREX')
        """
        market_context = self._get_market_context(target_market)
        
        return Agent(
            role="Technical Analyst",
            goal=f"Evaluate the technical setup of {market_context['asset_type']} to find assets with strong bullish or bearish signals.",
            backstory=f"A seasoned chartist specializing in {market_context['name']} markets who can spot technical patterns and strong signals from a mile away. {market_context['specifics']}",
            tools=[analyze_technical_setup_tool],
            llm=llm,
            verbose=True,
            allow_delegation=False,  # Disable delegation to reduce API calls
            max_iter=3  # Limit iterations to prevent runaway loops
        )

    def liquidity_filter_agent(self, llm, target_market: str = "US_EQUITY") -> Agent:
        """
        Create a liquidity filter agent for a specific market.
        
        ✅ PHASE 4 UPDATED: Agent now uses refactored tools (accepts symbol lists)
        
        Args:
            llm: Language model for the agent
            target_market: Market to analyze ('US_EQUITY', 'CRYPTO', 'FOREX')
        """
        market_context = self._get_market_context(target_market)
        
        return Agent(
            role="Liquidity and Risk Analyst",
            goal=f"Filter out illiquid or hard-to-trade {market_context['asset_type']} to ensure that trading is feasible and cost-effective.",
            backstory=f"A pragmatic analyst who ensures that every potential {market_context['name']} trade is backed by sufficient market liquidity and manageable spreads. {market_context['specifics']}",
            tools=[filter_by_liquidity_tool],
            llm=llm,
            verbose=True,
            allow_delegation=False,  # Disable delegation to reduce API calls
            max_iter=3  # Limit iterations to prevent runaway loops
        )

    def market_intelligence_chief(self, llm, target_market: str = "US_EQUITY") -> Agent:
        """
        Create a chief analyst agent for a specific market.
        
        ✅ PHASE 4 UPDATED: Agent coordinates refactored workflow
        
        Args:
            llm: Language model for the agent
            target_market: Market to analyze ('US_EQUITY', 'CRYPTO', 'FOREX')
        """
        market_context = self._get_market_context(target_market)
        
        return Agent(
            role="Chief of Market Intelligence",
            goal=f"Synthesize analyses from the volatility, technical, and liquidity agents to create a prioritized list of top {market_context['name']} trading opportunities.",
            backstory=f"The final decision-maker for {market_context['name']} markets, who weighs all the evidence to identify the most promising assets for the trading crew to focus on. {market_context['specifics']}",
            tools=[],
            llm=llm,
            verbose=True,
            allow_delegation=False,  # Disable delegation to reduce API calls
            max_iter=3  # Limit iterations to prevent runaway loops
        )

    @staticmethod
    def _get_market_context(market: str) -> dict:
        """
        Get market-specific context for agent descriptions.
        
        Args:
            market: Market type ('US_EQUITY', 'CRYPTO', 'FOREX')
            
        Returns:
            Dictionary with market context
        """
        contexts = {
            'US_EQUITY': {
                'name': 'US equity',
                'asset_type': 'stocks',
                'specifics': 'Understands market hours (9:30-4:00 ET), earnings impacts, and sector rotations.'
            },
            'CRYPTO': {
                'name': 'cryptocurrency',
                'asset_type': 'crypto assets',
                'specifics': 'Knows crypto trades 24/7, higher volatility, and different market dynamics than traditional assets.'
            },
            'FOREX': {
                'name': 'forex',
                'asset_type': 'currency pairs',
                'specifics': 'Expert in currency market dynamics, global economic factors, and 23/5 trading sessions.'
            }
        }
        return contexts.get(market, contexts['US_EQUITY'])
