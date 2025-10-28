from crewai import Crew, Process
from config.gemini_connector import gemini_manager
from agents.trading_agents import get_trading_agents
from tasks import get_trading_tasks

def create_trading_crew():
    """
    Creates and configures the trading crew.
    This function gets the LLM config, creates the agents with that config,
    creates the tasks, and assembles the final crew.
    """
    # Get the Gemini LLM configuration
    llm_config = gemini_manager.get_llm_config(model_name="gemini-pro")

    # Get the dictionary of trading agents, passing the config to the function
    agents = get_trading_agents(llm_config)

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
