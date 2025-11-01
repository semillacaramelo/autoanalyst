"""
Market Scanner Crew
This crew is responsible for scanning the market and identifying trading opportunities.
"""
from crewai import Crew, Process, Task, LLM
from pydantic import BaseModel, Field
from typing import List
import threading

from src.agents.scanner_agents import ScannerAgents
from src.connectors.gemini_connector_enhanced import enhanced_gemini_manager
from src.config.settings import settings
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

    def __init__(self, skip_init: bool = False):
        """
        Initialize the market scanner crew.
        
        Args:
            skip_init: If True, skip initialization (for help/validation commands)
        """
        if skip_init:
            self.volatility_analyzer = None
            self.technical_analyzer = None
            self.liquidity_filter = None
            self.chief_analyst = None
            return
            
        # Use enhanced Gemini connector with dynamic model selection
        model_name, api_key = enhanced_gemini_manager.get_llm_for_crewai()
        
        llm = LLM(
            model=model_name,
            api_key=api_key
        )
        agents_factory = ScannerAgents()

        # Define Agents
        self.volatility_analyzer = agents_factory.volatility_analyzer_agent(llm)
        self.technical_analyzer = agents_factory.technical_setup_agent(llm)
        self.liquidity_filter = agents_factory.liquidity_filter_agent(llm)
        self.chief_analyst = agents_factory.market_intelligence_chief(llm)

    def run(self):
        """Run the market scanner crew to identify trading opportunities."""
        if self.volatility_analyzer is None:
            raise RuntimeError("MarketScannerCrew was initialized with skip_init=True. Cannot run.")
            
        # Define Tasks
        fetch_and_analyze_volatility = Task(
            description="Fetch the S&P 100 symbols, get their daily data for the last 100 days, and analyze their volatility.",
            expected_output="A list of dictionaries, each containing a symbol and its volatility analysis.",
            agent=self.volatility_analyzer
        )

        analyze_technicals = Task(
            description="Based on the data from the volatility analysis, analyze the technical setup of each stock.",
            expected_output="A list of dictionaries, each containing a symbol and its technical score.",
            agent=self.technical_analyzer,
            context=[fetch_and_analyze_volatility]
        )

        filter_by_liquidity = Task(
            description="Filter the stocks by liquidity, ensuring they have an average daily volume of at least 1,000,000 shares.",
            expected_output="A list of dictionaries, each containing a symbol and its liquidity status.",
            agent=self.liquidity_filter,
            context=[fetch_and_analyze_volatility]
        )

        synthesize_results = Task(
            description="Synthesize the results from the volatility, technical, and liquidity analyses to create a prioritized list of the top 5 trading opportunities.",
            expected_output="A JSON object containing a 'top_assets' key, which is a list of dictionaries. Each dictionary should have 'symbol', 'priority', scores, 'recommended_strategies', and a 'reason'.",
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

def get_market_scanner_crew() -> MarketScannerCrew:
    """
    Get or create the global market scanner crew instance.
    Lazy initialization to avoid API calls during module import.
    Thread-safe using double-checked locking pattern.
    """
    global _market_scanner_crew_instance
    
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
