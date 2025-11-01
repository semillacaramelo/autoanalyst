"""
Trading Crew Orchestration

This module implements the main trading crew that executes the complete 4-agent
trading workflow. The crew uses CrewAI framework for multi-agent coordination
and follows a sequential process:

Agent Workflow:
    1. DataCollectorAgent: Fetches and validates OHLCV market data from Alpaca
    2. SignalGeneratorAgent: Applies trading strategy to generate BUY/SELL/HOLD signals
    3. RiskManagerAgent: Enforces position sizing and portfolio-level risk constraints
    4. ExecutionAgent: Places approved trades via Alpaca API (or logs in DRY_RUN mode)

Key Features:
    - Lazy initialization to avoid API calls during module import
    - Support for multiple trading strategies (3MA, RSI, MACD, Bollinger Bands)
    - Configurable timeframes and historical data limits
    - Built-in error handling and logging
    - DRY_RUN mode for safe testing

Usage:
    from src.crew.trading_crew import trading_crew
    
    # Execute crew for SPY with 3MA strategy
    result = trading_crew.run(
        symbol="SPY",
        strategy="3ma",
        timeframe="1Min",
        limit=100
    )
    
    # Check result
    if result['success']:
        print(f"Trade executed: {result['result']}")
    else:
        print(f"Error: {result['error']}")
"""
from crewai import Crew, Process
import threading
import logging

from src.agents.base_agents import TradingAgents
from src.config.settings import settings
from src.connectors.gemini_connector import gemini_manager
from src.crew.crew_context import crew_context
from src.crew.tasks import TradingTasks

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
            
        # Get LangChain LLM directly - CrewAI 1.3+ uses LangChain models directly
        llm = gemini_manager.get_client(skip_health_check=False)

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

        logger.info("TradingCrew initialized with LangChain LLM.")
    
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
_trading_crew_lock = threading.Lock()

def get_trading_crew() -> TradingCrew:
    """
    Get or create the global trading crew instance.
    Lazy initialization to avoid API calls during module import.
    Thread-safe using double-checked locking pattern.
    """
    global _trading_crew_instance
    
    if _trading_crew_instance is None:
        with _trading_crew_lock:
            # Double-check: another thread might have created instance while we waited
            if _trading_crew_instance is None:
                _trading_crew_instance = TradingCrew()
    
    return _trading_crew_instance

# For backwards compatibility, provide a proxy that lazily initializes
class _TradingCrewProxy:
    """
    Proxy that lazily initializes the trading crew on first access.
    
    Only the 'run' method is explicitly supported to maintain clear interface.
    Accessing other attributes will raise AttributeError.
    """
    def run(self, *args, **kwargs):
        """Execute the trading crew workflow."""
        return get_trading_crew().run(*args, **kwargs)
    
    def __getattr__(self, name):
        raise AttributeError(
            f"'_TradingCrewProxy' only supports the 'run' method. "
            f"Attribute '{name}' is not available."
        )

trading_crew = _TradingCrewProxy()
