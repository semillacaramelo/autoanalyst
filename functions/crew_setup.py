from crewai import Crew, Process
from config.gemini_connector import get_gemini_manager
from agents.trading_agents import get_trading_agents
from tasks import get_trading_tasks

def create_trading_crew():
    """
    Creates and configures the trading crew.
    This function gets the LLM config, creates the agents with that config,
    creates the tasks, and assembles the final crew.
    """
    # Get the Gemini manager instance using the factory function
    gemini_manager = get_gemini_manager()

    # Get the Gemini LLM configuration
    llm = gemini_manager.get_llm(model_name="gemini-1.5-pro-latest")

    # Get the dictionary of trading agents, passing the config to the function
    agents = get_trading_agents(llm)

    # Get the list of trading tasks, passing the agents to the function
    tasks = get_trading_tasks(agents)

    # --- Crew Definition ---
    trading_crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=2
    )

    return trading_crew
