"""
Trading Crew Orchestration
Main crew that executes the complete trading workflow.
"""
<<<<<<< HEAD
import os
=======
>>>>>>> 4fa32c2 (Apply patch /tmp/fa19928c-52d8-47c4-91a0-d51264a9e589.patch)
from crewai import Crew, Process
from crewai.llm import LLM
from src.agents.base_agents import TradingAgents
from src.crew.tasks import TradingTasks
from src.crew.crew_context import crew_context
<<<<<<< HEAD
=======
from src.connectors.gemini_connector import gemini_manager
>>>>>>> 4fa32c2 (Apply patch /tmp/fa19928c-52d8-47c4-91a0-d51264a9e589.patch)
from src.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class TradingCrew:
    """
    Main trading crew orchestrator.
    Manages the complete workflow from data collection to trade execution.
    """
    
    def __init__(self):
<<<<<<< HEAD
        os.environ["GEMINI_API_KEY"] = settings.get_gemini_keys_list()[0]
        llm = LLM(model=f"gemini/{settings.primary_llm_models[0]}")
=======
        # Get the resilient client from our custom manager
        resilient_client = gemini_manager.get_client()

        # Create the LLM adapter for CrewAI
        llm_adapter = LLM(
            model=f"gemini/{settings.primary_llm_models[0]}",
            llm=resilient_client
        )
>>>>>>> 4fa32c2 (Apply patch /tmp/fa19928c-52d8-47c4-91a0-d51264a9e589.patch)

        agents_factory = TradingAgents()
        tasks_factory = TradingTasks()

<<<<<<< HEAD
        data_collector_agent = agents_factory.data_collector_agent(llm)
        signal_generator_agent = agents_factory.signal_generator_agent(llm)
        risk_manager_agent = agents_factory.risk_manager_agent(llm)
        execution_agent = agents_factory.execution_agent(llm)
=======
        data_collector_agent = agents_factory.data_collector_agent(llm_adapter)
        signal_generator_agent = agents_factory.signal_generator_agent(llm_adapter)
        risk_manager_agent = agents_factory.risk_manager_agent(llm_adapter)
        execution_agent = agents_factory.execution_agent(llm_adapter)
>>>>>>> 4fa32c2 (Apply patch /tmp/fa19928c-52d8-47c4-91a0-d51264a9e589.patch)

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

<<<<<<< HEAD
# Global instance
=======
# Global instance for single runs, to be used by the orchestrator.
# Each thread will create its own instance.
>>>>>>> 4fa32c2 (Apply patch /tmp/fa19928c-52d8-47c4-91a0-d51264a9e589.patch)
trading_crew = TradingCrew()
