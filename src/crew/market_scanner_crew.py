"""
Market Scanner Crew

✅ PHASE 4 REFACTORED (November 4, 2025)
========================================

STATUS: FUNCTIONAL - Architecture refactored to use Independent Tool Fetching pattern

CHANGES IMPLEMENTED:
--------------------
1. Tools refactored to accept List[str] (symbol names) instead of Dict[str, DataFrame]
2. Each tool fetches its own data internally using AlpacaConnector
3. Tools return JSON-serializable results (List[Dict] with primitives)
4. Task descriptions updated to guide LLM through new workflow
5. No DataFrame passing between agents - all data fetched independently

ARCHITECTURE PATTERN:
--------------------
Independent Tool Fetching (Option A from CREWAI_REFERENCE.md)
- Simplest and most reliable pattern for CrewAI
- Each tool is self-sufficient
- Tool parameters are JSON-serializable (List[str], str, int, float)
- Tool results are JSON-serializable (List[Dict] with primitives)

WORKFLOW:
---------
1. VolatilityAnalyzer: Get symbols → analyze_volatility(symbols) → Returns volatility metrics
2. TechnicalAnalyst: Extract symbols → analyze_technical_setup(symbols) → Returns tech scores
3. LiquidityFilter: Extract symbols → filter_by_liquidity(symbols) → Returns liquidity data
4. ChiefAnalyst: Synthesize all results → Returns top 5 prioritized opportunities

All data fetching happens INSIDE each tool - no data passing between agents.

TESTING:
--------
Ready for integration testing with real market data.
Expected: Scanner should find 1-3 opportunities (vs 0 with old architecture).

See docs/CREWAI_REFERENCE.md for complete architecture documentation.

========================================

This crew is responsible for scanning the market and identifying trading opportunities.
"""
from crewai import Crew, Process, Task, LLM
from pydantic import BaseModel, Field
from typing import List, Optional
import threading
from datetime import datetime
import pytz

from src.agents.scanner_agents import ScannerAgents
from src.connectors.gemini_connector_enhanced import enhanced_gemini_manager
from src.config.settings import settings
from src.utils.market_calendar import MarketCalendar
import json


class AssetAnalysis(BaseModel):
    """Pydantic model for a single asset analysis."""
    symbol: str = Field(..., description="The stock symbol.")
    priority: int = Field(..., description="The priority of the asset for trading.")
    scores: dict = Field(..., description="A dictionary of scores (volatility, technical, liquidity).")
    recommended_strategies: List[str] = Field(..., description="A list of recommended trading strategies.")
    reason: str = Field(..., description="The reasoning behind the recommendation.")

class TopAssetsResponse(BaseModel):
    """Pydantic model for the top assets response."""
    top_assets: List[AssetAnalysis] = Field(..., description="A list of the top assets to trade.")


class MarketScannerCrew:

    def __init__(self, target_market: Optional[str] = None, skip_init: bool = False):
        """
        Initialize the market scanner crew.
        
        Args:
            target_market: Market to scan ('US_EQUITY', 'CRYPTO', 'FOREX', or None for auto-detect)
            skip_init: If True, skip initialization (for help/validation commands)
        """
        if skip_init:
            self.volatility_analyzer = None
            self.technical_analyzer = None
            self.liquidity_filter = None
            self.chief_analyst = None
            self.target_market = None
            return
        
        # Auto-detect active market if not specified
        if target_market is None:
            market_calendar = MarketCalendar()
            # Prioritize US equity during market hours, otherwise default to crypto (24/7)
            active_markets = market_calendar.get_active_markets(
                datetime.now(pytz.utc), ['US_EQUITY', 'CRYPTO']
            )
            if 'US_EQUITY' in active_markets:
                self.target_market = 'US_EQUITY'
            else:
                self.target_market = 'CRYPTO'
        else:
            self.target_market = target_market
            
        # Use enhanced Gemini connector with dynamic model selection and auto-rotation
        # Market scanner makes many API calls (analyzing 100+ stocks across 4 agents)
        # Auto-rotate enables efficient use of all available API keys without waiting
        model_name, api_key = enhanced_gemini_manager.get_llm_for_crewai(
            estimated_requests=8,
            auto_rotate=True  # Enable automatic key rotation for intensive operations
        )
        
        llm = LLM(
            model=model_name,
            api_key=api_key
        )
        agents_factory = ScannerAgents()

        # Define Agents with market-specific context
        self.volatility_analyzer = agents_factory.volatility_analyzer_agent(llm, self.target_market)
        self.technical_analyzer = agents_factory.technical_setup_agent(llm, self.target_market)
        self.liquidity_filter = agents_factory.liquidity_filter_agent(llm, self.target_market)
        self.chief_analyst = agents_factory.market_intelligence_chief(llm, self.target_market)

    def run(self, max_symbols: Optional[int] = None):
        """
        Run the market scanner crew to identify trading opportunities.
        
        ✅ PHASE 4 REFACTORED (November 4, 2025)
        ----------------------------------------
        Tasks updated to use Independent Tool Fetching pattern.
        Tools now accept symbol lists (List[str]) instead of DataFrames.
        
        Args:
            max_symbols: Maximum number of symbols to scan (None for all in universe)
        """
        if self.volatility_analyzer is None:
            raise RuntimeError("MarketScannerCrew was initialized with skip_init=True. Cannot run.")
        
        # Get market-specific task descriptions
        market_names = {
            'US_EQUITY': 'S&P 100 stocks',
            'CRYPTO': 'cryptocurrency pairs',
            'FOREX': 'major currency pairs'
        }
        asset_name = market_names.get(self.target_market, 'assets')
        symbol_limit = f"top {max_symbols}" if max_symbols else "all available"
            
        # Define Tasks with refactored workflow (Phase 4)
        # Task 1: Get symbols and analyze volatility in one step
        fetch_and_analyze_volatility = Task(
            description=f"""
Get {symbol_limit} symbols from the {self.target_market} market and analyze their volatility.

WORKFLOW:
1. Use get_universe_symbols tool with market='{self.target_market}' to get symbol list
2. Use analyze_volatility tool with the symbols list (tool will fetch data internally)

The analyze_volatility tool is self-sufficient - just pass it the list of symbol strings.
DO NOT try to fetch data separately first.

Example:
symbols = get_universe_symbols(market='{self.target_market}', max_symbols={max_symbols or 'None'})
results = analyze_volatility(symbols=symbols, timeframe='1Hour', limit=100)
""",
            expected_output=f"A list of dictionaries with volatility metrics: symbol, atr, volatility_score, status for {asset_name}.",
            agent=self.volatility_analyzer
        )

        # Task 2: Analyze technical setup for symbols that passed volatility
        analyze_technicals = Task(
            description=f"""
Analyze the technical setup for symbols from the volatility analysis.

WORKFLOW:
1. Extract successful symbols from previous analysis (where status='success')
2. Use analyze_technical_setup tool with the symbols list (tool fetches data internally)

The tool is self-sufficient - pass symbols as List[str], it will fetch data and calculate indicators.

Example:
successful_symbols = [item['symbol'] for item in volatility_results if item.get('status') == 'success']
tech_results = analyze_technical_setup(symbols=successful_symbols, timeframe='1Day', limit=100)
""",
            expected_output=f"A list of dictionaries with technical scores: symbol, technical_score, reason, indicators, status for {asset_name}.",
            agent=self.technical_analyzer,
            context=[fetch_and_analyze_volatility]
        )

        # Task 3: Filter by liquidity for symbols that passed technical
        filter_by_liquidity = Task(
            description=f"""
Filter symbols by liquidity (average trading volume).

WORKFLOW:
1. Extract successful symbols from technical analysis (where status='success')
2. Use filter_by_liquidity tool with the symbols list (tool fetches data internally)

The tool is self-sufficient - pass symbols as List[str], it will fetch volume data.

Example:
tech_symbols = [item['symbol'] for item in tech_results if item.get('status') == 'success']
liq_results = filter_by_liquidity(symbols=tech_symbols, min_volume=1000000, timeframe='1Day')
""",
            expected_output=f"A list of dictionaries with liquidity metrics: symbol, avg_volume, liquidity_score, is_liquid, status for {asset_name}.",
            agent=self.liquidity_filter,
            context=[analyze_technicals]
        )

        # Task 4: Synthesize and prioritize results
        synthesize_results = Task(
            description=f"""
Synthesize results from all analyses to create a prioritized list of top 5 trading opportunities.

WORKFLOW:
1. Combine results from volatility, technical, and liquidity analyses
2. Calculate composite scores (e.g., (volatility_score + technical_score + liquidity_score) / 3)
3. Filter to liquid assets only (is_liquid = true)
4. Sort by composite score (highest first)
5. Select top 5 symbols
6. Recommend 1-2 strategies per symbol based on technical indicators
   - High RSI (>70): bollinger_bands_reversal
   - Low RSI (<30): rsi_breakout
   - MACD crossover: macd
   - Strong trend: 3ma

Create a well-formatted JSON response with the top 5 opportunities.
""",
            expected_output=f"JSON object with 'top_assets' list containing symbol, priority, scores, recommended_strategies, and reason for top 5 {asset_name}.",
            agent=self.chief_analyst,
            context=[fetch_and_analyze_volatility, analyze_technicals, filter_by_liquidity],
            output_json=TopAssetsResponse
        )

        # Assemble the Crew
        scanner_crew = Crew(
            agents=[self.volatility_analyzer, self.technical_analyzer, self.liquidity_filter, self.chief_analyst],
            tasks=[fetch_and_analyze_volatility, analyze_technicals, filter_by_liquidity, synthesize_results],
            process=Process.sequential,
            verbose=True
        )

        result = scanner_crew.kickoff()
        return result

# Global instance factory function for lazy initialization
_market_scanner_crew_instance = None
_market_scanner_crew_lock = threading.Lock()

def get_market_scanner_crew(target_market: Optional[str] = None) -> MarketScannerCrew:
    """
    Get or create the global market scanner crew instance.
    Lazy initialization to avoid API calls during module import.
    Thread-safe using double-checked locking pattern.
    
    Args:
        target_market: Market to scan ('US_EQUITY', 'CRYPTO', 'FOREX', or None for auto-detect)
    """
    global _market_scanner_crew_instance
    
    # Note: For different markets, create new instances (not cached)
    # Only cache for default (auto-detect) behavior
    if target_market is not None:
        return MarketScannerCrew(target_market=target_market)
    
    if _market_scanner_crew_instance is None:
        with _market_scanner_crew_lock:
            # Double-check: another thread might have created instance while we waited
            if _market_scanner_crew_instance is None:
                _market_scanner_crew_instance = MarketScannerCrew()
    
    return _market_scanner_crew_instance

# For backwards compatibility, provide a proxy that lazily initializes
class _MarketScannerCrewProxy:
    """
    Proxy that lazily initializes the market scanner crew on first access.
    
    Only the 'run' method is explicitly supported to maintain clear interface.
    Accessing other attributes will raise AttributeError.
    """
    def run(self, *args, **kwargs):
        """Run the market scanner crew to identify opportunities."""
        return get_market_scanner_crew().run(*args, **kwargs)
    
    def __getattr__(self, name):
        raise AttributeError(
            f"'_MarketScannerCrewProxy' only supports the 'run' method. "
            f"Attribute '{name}' is not available."
        )

market_scanner_crew = _MarketScannerCrewProxy()
