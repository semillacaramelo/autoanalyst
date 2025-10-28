from crewai import Crew, Process
from config.gemini_connector import gemini_manager
from agents.trading_agents import get_trading_agents
from tasks import get_trading_tasks

def create_trading_crew():
    """
    Creates and configures the trading crew.
    This function initializes the LLM, creates the agents with the LLM,
    creates the tasks, and assembles the final crew.
    """
    # Get a Gemini LLM instance from our dedicated manager
    gemini_llm = gemini_manager.get_llm(model_name="gemini-pro")

    # Get the dictionary of trading agents, passing the LLM to the function
    agents = get_trading_agents(gemini_llm)

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
