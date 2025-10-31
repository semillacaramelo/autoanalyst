"""
Trading Crew Orchestration
Main crew that executes the complete trading workflow.
"""
import os
from crewai import Crew, Process
from crewai.llm import LLM
from src.agents.base_agents import TradingAgents
from src.crew.tasks import TradingTasks
from src.crew.crew_context import crew_context
from src.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class TradingCrew:
    """
    Main trading crew orchestrator.
    Manages the complete workflow from data collection to trade execution.
    """
    
    def __init__(self):
        os.environ["GEMINI_API_KEY"] = settings.get_gemini_keys_list()[0]
        llm = LLM(model=f"gemini/{settings.primary_llm_models[0]}")

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
            "limit": limit
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

# Global instance for single runs
trading_crew = TradingCrew()
