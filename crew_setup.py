from crewai import Crew, Process
from config.gemini_connector import gemini_manager
from agents.trading_agents import get_trading_agents
from tasks import get_trading_tasks

def create_trading_crew():
    """
    Creates and configures the trading crew.
    This function initializes the agents, configures the LLM, creates the tasks,
    and assembles the final crew.
    """
    # Get the dictionary of trading agents
    agents = get_trading_agents()

    # Get a Gemini LLM instance from our dedicated manager
    gemini_llm = gemini_manager.get_llm(model_name="gemini-pro")

    # Assign the configured LLM to each agent
    for agent in agents.values():
        agent.llm = gemini_llm

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
