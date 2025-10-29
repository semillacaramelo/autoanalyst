"""
Trading Crew Orchestration
Main crew that executes the complete trading workflow.
"""

from crewai import Crew, Process
from src.crew.tasks import (
    collect_data_task,
    # ...other tasks as per plan...
    execute_trade_task
)
from src.agents.base_agents import (
    data_collector_agent,
    # ...other agents as per plan...
    execution_agent
)
"""
Trading Crew Orchestration
Main crew that executes the complete trading workflow.
"""

from crewai import Crew, Process
from src.crew.tasks import (
    collect_data_task,
    generate_signal_task,
    validate_signal_task,
    assess_risk_task,
    execute_trade_task
)
from src.agents.base_agents import (
    data_collector_agent,
    signal_generator_agent,
    signal_validator_agent,
    risk_manager_agent,
    execution_agent
)
from src.config.settings import settings
import logging
from src.connectors.gemini_connector import gemini_manager

logger = logging.getLogger(__name__)


class TradingCrew:
    """
    Main trading crew orchestrator.
    Manages the complete workflow from data collection to trade execution.
    """
    
    def __init__(self):

        self.crew = Crew(
            agents=[
                data_collector_agent,
                signal_generator_agent,
                signal_validator_agent,
                risk_manager_agent,
                execution_agent
            ],
            tasks=[
                collect_data_task,
                generate_signal_task,
                validate_signal_task,
                assess_risk_task,
                execute_trade_task
            ],
            process=Process.sequential,  # Execute tasks in order
            verbose=True
        )

        logger.info("TradingCrew initialized")
    
    def run(
        self,
        symbol: str = None,
        timeframe: str = "1Min",
        limit: int = 100
    ) -> dict:
        """
        Execute the complete trading workflow.
        
        Args:
            symbol: Stock symbol to trade (defaults to settings)
            timeframe: Bar timeframe
            limit: Number of historical bars to analyze
        
        Returns:
            Dictionary with crew execution results
        """
        # Use configured symbol if not provided
        if symbol is None:
            symbol = settings.trading_symbol
        
        logger.info(f"Starting trading crew for {symbol}")
        logger.info(f"Configuration: timeframe={timeframe}, bars={limit}")
        logger.info(f"Mode: {'DRY RUN' if settings.dry_run else 'LIVE TRADING'}")
        
        # Prepare inputs for tasks (template variables)
        inputs = {
            "symbol": symbol,
            "timeframe": timeframe,
            "limit": limit,
            "ma_fast": settings.ma_fast_period,
            "ma_medium": settings.ma_medium_period,
            "ma_slow": settings.ma_slow_period,
            "volume_threshold": settings.volume_threshold,
            "adx_threshold": settings.adx_threshold,
            "max_positions": settings.max_open_positions,
            "max_risk": settings.max_risk_per_trade * 100,
            "daily_loss": settings.daily_loss_limit * 100
        }
        
        try:
            # Execute the crew
            result = self.crew.kickoff(inputs=inputs)
            
            logger.info("Trading crew completed successfully")
            logger.info(f"Result: {result}")
            
            return {
                "success": True,
                "result": str(result),
                "symbol": symbol,
                "configuration": inputs
            }
        
        except Exception as e:
            logger.error(f"Trading crew execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol
            }


# Global instance
trading_crew = TradingCrew()
