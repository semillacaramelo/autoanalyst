"""
Market Scanner Crew
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
            
        # Define Tasks with market-aware descriptions
        fetch_and_analyze_volatility = Task(
            description=f"Fetch {symbol_limit} symbols from the {self.target_market} market, get their historical data, and analyze their volatility. Use the get_universe_symbols tool with market='{self.target_market}' to get the symbol list.",
            expected_output=f"A list of dictionaries, each containing a symbol and its volatility analysis for {asset_name}.",
            agent=self.volatility_analyzer
        )

        analyze_technicals = Task(
            description=f"Based on the data from the volatility analysis, analyze the technical setup of each {self.target_market} asset.",
            expected_output=f"A list of dictionaries, each containing a symbol and its technical score for {asset_name}.",
            agent=self.technical_analyzer,
            context=[fetch_and_analyze_volatility]
        )

        filter_by_liquidity = Task(
            description=f"Filter the {asset_name} by liquidity, ensuring they have sufficient trading volume for the {self.target_market} market.",
            expected_output=f"A list of dictionaries, each containing a symbol and its liquidity status for {asset_name}.",
            agent=self.liquidity_filter,
            context=[fetch_and_analyze_volatility]
        )

        synthesize_results = Task(
            description=f"Synthesize the results from the volatility, technical, and liquidity analyses to create a prioritized list of the top 5 {self.target_market} trading opportunities.",
            expected_output=f"A JSON object containing a 'top_assets' key, which is a list of dictionaries. Each dictionary should have 'symbol', 'priority', scores, 'recommended_strategies', and a 'reason' for {asset_name}.",
            agent=self.chief_analyst,
            context=[analyze_technicals, filter_by_liquidity],
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
