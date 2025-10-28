from crewai import Agent, Crew, Process
from config.gemini_connector import gemini_manager
from agents.trading_agents import (
    asset_selector,
    trend_analyzer,
    signal_confirmer,
    trade_executor,
    performance_analyzer,
    strategy_enhancer
)
from tasks import (
    select_asset_task,
    analyze_trend_task,
    confirm_signal_task,
    execute_trade_task
)

# --- LLM Configuration ---
# Get a Gemini LLM instance from our dedicated manager
# This single LLM instance can be shared across all agents
gemini_llm = gemini_manager.get_llm(model_name="gemini-pro")


# --- Agent Definition Enhancement ---
# Assign the configured LLM to each agent.
asset_selector.llm = gemini_llm
trend_analyzer.llm = gemini_llm
signal_confirmer.llm = gemini_llm
trade_executor.llm = gemini_llm
performance_analyzer.llm = gemini_llm
strategy_enhancer.llm = gemini_llm


# --- Crew Definition ---
trading_crew = Crew(
    agents=[
        asset_selector,
        trend_analyzer,
        signal_confirmer,
        trade_executor,
        performance_analyzer,
        strategy_enhancer
    ],
    tasks=[
        select_asset_task,
        analyze_trend_task,
        confirm_signal_task,
        execute_trade_task,
    ],
    process=Process.sequential,
    verbose=2
)

# To run the crew, you would use the following code in a main.py file:
# if __name__ == "__main__":
#     result = trading_crew.kickoff(inputs={'assets_of_interest': ['SPY', 'QQQ']})
#     print(result)
