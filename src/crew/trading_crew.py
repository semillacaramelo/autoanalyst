"""
Trading Crew Orchestration
Main crew that executes the complete trading workflow.
"""
from crewai import Crew, Process
from crewai.llm import LLM

from src.agents.base_agents import TradingAgents
from src.config.settings import settings
from src.connectors.gemini_connector import gemini_manager
from src.crew.crew_context import crew_context
from src.crew.tasks import TradingTasks
import logging

logger = logging.getLogger(__name__)

class TradingCrew:
    """
    Main trading crew orchestrator.
    Manages the complete workflow from data collection to trade execution.
    """
    
    def __init__(self, skip_init: bool = False):
        """
        Initialize the trading crew.
        
        Args:
            skip_init: If True, skip initialization (for help/validation commands)
        """
        if skip_init:
            self.crew = None
            return
            
        llm_client = gemini_manager.get_client()
        llm = LLM(llm=llm_client, model=f"gemini/{settings.primary_llm_models[0]}")

        agents_factory = TradingAgents()
        tasks_factory = TradingTasks()

        data_collector_agent = agents_factory.data_collector_agent(llm)
        signal_generator_agent = agents_factory.signal_generator_agent(llm)
        risk_manager_agent = agents_factory.risk_manager_agent(llm)
        execution_agent = agents_factory.execution_agent(llm)

        collect_data = tasks_factory.collect_data_task(data_collector_agent)
        generate_signal = tasks_factory.generate_signal_task(signal_generator_agent, context=[collect_data])
        assess_risk = tasks_factory.assess_risk_task(risk_manager_agent, context=[generate_signal])
        execute_trade = tasks_factory.execute_trade_task(execution_agent, context=[assess_risk])

        self.crew = Crew(
            agents=[
                data_collector_agent,
                signal_generator_agent,
                risk_manager_agent,
                execution_agent
            ],
            tasks=[
                collect_data,
                generate_signal,
                assess_risk,
                execute_trade
            ],
            process=Process.sequential,
            verbose=True
        )

        logger.info("TradingCrew initialized with dependency injection.")
    
    def run(
        self,
        symbol: str = None,
        strategy: str = "3ma",
        timeframe: str = "1Min",
        limit: int = 100
    ) -> dict:
        """
        Execute the complete trading workflow.
        """
        if self.crew is None:
            raise RuntimeError("TradingCrew was initialized with skip_init=True. Cannot run.")
            
        if symbol is None:
            symbol = settings.trading_symbol
        
        logger.info(f"Starting trading crew for {symbol} with strategy {strategy}")
        logger.info(f"Configuration: timeframe={timeframe}, bars={limit}")
        logger.info(f"Mode: {'DRY RUN' if settings.dry_run else 'LIVE TRADING'}")
        
        crew_context.market_data = None

        inputs = {
            "symbol": symbol,
            "strategy_name": strategy,
            "timeframe": timeframe,
            "limit": limit,
            "max_positions": settings.max_open_positions,
            "max_risk": settings.max_risk_per_trade,
            "daily_loss": settings.daily_loss_limit,
        }
        
        try:
            result = self.crew.kickoff(inputs=inputs)
            
            logger.info("Trading crew completed successfully")
            logger.info(f"Result: {result}")
            
            return {
                "success": True,
                "result": str(result),
                "symbol": symbol,
                "strategy": strategy,
                "configuration": inputs
            }
        
        except Exception as e:
            logger.error(f"Trading crew execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "strategy": strategy
            }

# Global instance factory function for lazy initialization
_trading_crew_instance = None

def get_trading_crew() -> TradingCrew:
    """
    Get or create the global trading crew instance.
    Lazy initialization to avoid API calls during module import.
    """
    global _trading_crew_instance
    if _trading_crew_instance is None:
        _trading_crew_instance = TradingCrew()
    return _trading_crew_instance

# For backwards compatibility, provide a property-like accessor
class _TradingCrewProxy:
    """Proxy that lazily initializes the trading crew on first access."""
    def __getattr__(self, name):
        return getattr(get_trading_crew(), name)
    
    def run(self, *args, **kwargs):
        return get_trading_crew().run(*args, **kwargs)

trading_crew = _TradingCrewProxy()
